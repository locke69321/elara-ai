from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from apps.api.agents.policy import Capability

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
    def __init__(self) -> None:
        self._requests: dict[str, ApprovalRequest] = {}

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
        self._requests[request.id] = request
        return request

    def decide_request(
        self,
        *,
        approval_id: str,
        approver_id: str,
        decision: ApprovalDecision,
    ) -> ApprovalRequest:
        request = self._requests.get(approval_id)
        if request is None:
            raise ValueError("approval request not found")
        if request.status != "pending":
            raise ValueError("approval request is already decided")

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
        self._requests[approval_id] = decided
        return decided

    def get_request(self, *, approval_id: str) -> ApprovalRequest | None:
        return self._requests.get(approval_id)

    def list_requests(
        self,
        *,
        workspace_id: str,
        status: ApprovalStatus | None = None,
    ) -> list[ApprovalRequest]:
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
        request = self._requests.get(approval_id)
        if request is None:
            return False

        return (
            request.workspace_id == workspace_id
            and request.actor_id == actor_id
            and request.capability == capability
            and request.action == action
            and request.status == "approved"
        )
