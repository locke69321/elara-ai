import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from apps.api.agents.policy import Capability
from apps.api.db.state import connect_state_db

ApprovalStatus = Literal["pending", "approved", "denied"]
ApprovalDecision = Literal["approved", "denied"]


@dataclass(frozen=True)
class ApprovalRequest:
    id: str
    workspace_id: str
    actor_id: str
    capability: Capability
    action: str
    reason: str
    status: ApprovalStatus
    created_at: str
    decided_at: str | None
    decided_by: str | None


class ApprovalRequiredError(PermissionError):
    def __init__(self, approval_id: str, message: str = "approval required") -> None:
        super().__init__(message)
        self.approval_id = approval_id


class ApprovalService:
    def __init__(
        self,
        *,
        database_path: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._connection = connection
        self._owns_connection = False
        if self._connection is None and database_path is not None:
            self._connection = connect_state_db(database_path)
            self._owns_connection = True
        self._requests: dict[str, ApprovalRequest] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    def _from_row(self, row: tuple[object, ...]) -> ApprovalRequest:
        return ApprovalRequest(
            id=str(row[0]),
            workspace_id=str(row[1]),
            actor_id=str(row[2]),
            capability=str(row[3]),
            action=str(row[4]),
            reason=str(row[5]),
            status=str(row[6]),
            created_at=str(row[7]),
            decided_at=None if row[8] is None else str(row[8]),
            decided_by=None if row[9] is None else str(row[9]),
        )

    def create_request(
        self,
        *,
        workspace_id: str,
        actor_id: str,
        capability: Capability,
        action: str,
        reason: str,
    ) -> ApprovalRequest:
        request = ApprovalRequest(
            id=f"approval-{uuid4()}",
            workspace_id=workspace_id,
            actor_id=actor_id,
            capability=capability,
            action=action,
            reason=reason,
            status="pending",
            created_at=datetime.now(timezone.utc).isoformat(),
            decided_at=None,
            decided_by=None,
        )
        if self._connection is None:
            self._requests[request.id] = request
        else:
            self._connection.execute(
                """
                insert into approval_request_record (
                  id, workspace_id, actor_id, capability, action, reason, status,
                  created_at, decided_at, decided_by
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    request.id,
                    request.workspace_id,
                    request.actor_id,
                    request.capability,
                    request.action,
                    request.reason,
                    request.status,
                    request.created_at,
                    request.decided_at,
                    request.decided_by,
                ),
            )
            self._connection.commit()
        return request

    def decide_request(
        self,
        *,
        approval_id: str,
        approver_id: str,
        decision: ApprovalDecision,
    ) -> ApprovalRequest:
        request = self.get_request(approval_id=approval_id)
        if request is None:
            raise ValueError("approval request not found")
        if request.status != "pending":
            raise ValueError("approval request is already decided")
        if approver_id != request.actor_id:
            raise PermissionError("approver is not authorized for this approval request")

        decided = ApprovalRequest(
            id=request.id,
            workspace_id=request.workspace_id,
            actor_id=request.actor_id,
            capability=request.capability,
            action=request.action,
            reason=request.reason,
            status=decision,
            created_at=request.created_at,
            decided_at=datetime.now(timezone.utc).isoformat(),
            decided_by=approver_id,
        )
        if self._connection is None:
            self._requests[approval_id] = decided
        else:
            self._connection.execute(
                """
                update approval_request_record
                set status = ?, decided_at = ?, decided_by = ?
                where id = ?
                """,
                (decided.status, decided.decided_at, decided.decided_by, approval_id),
            )
            self._connection.commit()
        return decided

    def get_request(self, *, approval_id: str) -> ApprovalRequest | None:
        if self._connection is not None:
            cursor = self._connection.execute(
                """
                select id, workspace_id, actor_id, capability, action, reason, status,
                       created_at, decided_at, decided_by
                from approval_request_record
                where id = ?
                """,
                (approval_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return self._from_row(row)
        return self._requests.get(approval_id)

    def list_requests(
        self,
        *,
        workspace_id: str,
        status: ApprovalStatus | None = None,
    ) -> list[ApprovalRequest]:
        if self._connection is not None:
            if status is None:
                cursor = self._connection.execute(
                    """
                    select id, workspace_id, actor_id, capability, action, reason, status,
                           created_at, decided_at, decided_by
                    from approval_request_record
                    where workspace_id = ?
                    order by created_at asc
                    """,
                    (workspace_id,),
                )
            else:
                cursor = self._connection.execute(
                    """
                    select id, workspace_id, actor_id, capability, action, reason, status,
                           created_at, decided_at, decided_by
                    from approval_request_record
                    where workspace_id = ? and status = ?
                    order by created_at asc
                    """,
                    (workspace_id, status),
                )
            rows = cursor.fetchall()
            return [self._from_row(row) for row in rows]

        requests = [
            request
            for request in self._requests.values()
            if request.workspace_id == workspace_id
        ]
        if status is not None:
            requests = [request for request in requests if request.status == status]
        return sorted(requests, key=lambda request: request.created_at)

    def is_approved(
        self,
        *,
        approval_id: str,
        workspace_id: str,
        actor_id: str,
        capability: Capability,
        action: str,
    ) -> bool:
        request = self.get_request(approval_id=approval_id)
        if request is None:
            return False

        return (
            request.workspace_id == workspace_id
            and request.actor_id == actor_id
            and request.capability == capability
            and request.action == action
            and request.status == "approved"
        )
