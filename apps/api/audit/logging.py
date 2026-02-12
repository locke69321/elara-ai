import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from apps.api.db.state import connect_state_db


@dataclass(frozen=True)
class AuditEvent:
    id: str
    workspace_id: str
    actor_id: str
    action: str
    outcome: str
    metadata: dict[str, object]
    previous_hash: str
    event_hash: str
    created_at: str


class ImmutableAuditLog:
    """Append-only audit log with hash chaining for tamper evidence."""

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
        self._events_by_workspace: dict[str, list[AuditEvent]] = {}
        self._last_hash_by_workspace: dict[str, str] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    @staticmethod
    def _serialize_payload(
        *,
        workspace_id: str,
        actor_id: str,
        action: str,
        outcome: str,
        metadata: dict[str, object],
        created_at: str,
    ) -> str:
        event_payload = {
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "action": action,
            "outcome": outcome,
            "metadata": metadata,
            "created_at": created_at,
        }
        return json.dumps(event_payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _hash_event(*, previous_hash: str, serialized_payload: str) -> str:
        return hashlib.sha256(f"{previous_hash}:{serialized_payload}".encode("utf-8")).hexdigest()

    def _last_hash_for_workspace(self, *, workspace_id: str) -> str:
        if self._connection is None:
            return self._last_hash_by_workspace.get(workspace_id, "")

        cursor = self._connection.execute(
            """
            select event_hash
            from audit_event_record
            where workspace_id = ?
            order by created_at desc
            limit 1
            """,
            (workspace_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return ""
        return str(row[0])

    def append_event(
        self,
        *,
        workspace_id: str,
        actor_id: str,
        action: str,
        outcome: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        previous_hash = self._last_hash_for_workspace(workspace_id=workspace_id)
        payload = metadata or {}
        created_at = datetime.now(timezone.utc).isoformat()

        serialized = self._serialize_payload(
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            outcome=outcome,
            metadata=payload,
            created_at=created_at,
        )
        event_hash = self._hash_event(previous_hash=previous_hash, serialized_payload=serialized)

        event = AuditEvent(
            id=f"audit-{uuid4()}",
            workspace_id=workspace_id,
            actor_id=actor_id,
            action=action,
            outcome=outcome,
            metadata=payload,
            previous_hash=previous_hash,
            event_hash=event_hash,
            created_at=created_at,
        )

        if self._connection is None:
            workspace_events = self._events_by_workspace.setdefault(workspace_id, [])
            workspace_events.append(event)
            self._last_hash_by_workspace[workspace_id] = event_hash
        else:
            self._connection.execute(
                """
                insert into audit_event_record (
                  id, workspace_id, actor_id, action, outcome, metadata_json,
                  previous_hash, event_hash, created_at
                ) values (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.workspace_id,
                    event.actor_id,
                    event.action,
                    event.outcome,
                    json.dumps(event.metadata, sort_keys=True),
                    event.previous_hash,
                    event.event_hash,
                    event.created_at,
                ),
            )
            self._connection.commit()
        return event

    def list_events(self, *, workspace_id: str, limit: int = 100) -> list[AuditEvent]:
        if self._connection is None:
            return self._events_by_workspace.get(workspace_id, [])[-limit:]

        cursor = self._connection.execute(
            """
            select id, workspace_id, actor_id, action, outcome, metadata_json,
                   previous_hash, event_hash, created_at
            from audit_event_record
            where workspace_id = ?
            order by created_at desc
            limit ?
            """,
            (workspace_id, limit),
        )
        rows = list(reversed(cursor.fetchall()))
        return [
            AuditEvent(
                id=str(row[0]),
                workspace_id=str(row[1]),
                actor_id=str(row[2]),
                action=str(row[3]),
                outcome=str(row[4]),
                metadata=json.loads(str(row[5])),
                previous_hash=str(row[6]),
                event_hash=str(row[7]),
                created_at=str(row[8]),
            )
            for row in rows
        ]

    def verify_chain(self, *, workspace_id: str) -> bool:
        events = self.list_events(workspace_id=workspace_id, limit=1_000_000)
        previous_hash = ""

        for event in events:
            serialized = self._serialize_payload(
                workspace_id=event.workspace_id,
                actor_id=event.actor_id,
                action=event.action,
                outcome=event.outcome,
                metadata=event.metadata,
                created_at=event.created_at,
            )
            computed_hash = self._hash_event(
                previous_hash=previous_hash,
                serialized_payload=serialized,
            )

            if event.previous_hash != previous_hash:
                return False
            if event.event_hash != computed_hash:
                return False
            previous_hash = event.event_hash

        return True
