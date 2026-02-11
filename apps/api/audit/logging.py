import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4


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

    def __init__(self) -> None:
        self._events_by_workspace: dict[str, list[AuditEvent]] = {}
        self._last_hash_by_workspace: dict[str, str] = {}

    def append_event(
        self,
        *,
        workspace_id: str,
        actor_id: str,
        action: str,
        outcome: str,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        previous_hash = self._last_hash_by_workspace.get(workspace_id, "")
        payload = metadata or {}
        created_at = datetime.now(timezone.utc).isoformat()

        event_payload = {
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "action": action,
            "outcome": outcome,
            "metadata": payload,
            "created_at": created_at,
        }
        serialized = json.dumps(event_payload, sort_keys=True, separators=(",", ":"))
        event_hash = hashlib.sha256(f"{previous_hash}:{serialized}".encode("utf-8")).hexdigest()

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

        workspace_events = self._events_by_workspace.setdefault(workspace_id, [])
        workspace_events.append(event)
        self._last_hash_by_workspace[workspace_id] = event_hash
        return event

    def list_events(self, *, workspace_id: str, limit: int = 100) -> list[AuditEvent]:
        return self._events_by_workspace.get(workspace_id, [])[-limit:]

    def verify_chain(self, *, workspace_id: str) -> bool:
        events = self._events_by_workspace.get(workspace_id, [])
        previous_hash = ""

        for event in events:
            payload = {
                "workspace_id": event.workspace_id,
                "actor_id": event.actor_id,
                "action": event.action,
                "outcome": event.outcome,
                "metadata": event.metadata,
                "created_at": event.created_at,
            }
            serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            computed_hash = hashlib.sha256(
                f"{previous_hash}:{serialized}".encode("utf-8")
            ).hexdigest()

            if event.previous_hash != previous_hash:
                return False
            if event.event_hash != computed_hash:
                return False
            previous_hash = event.event_hash

        return True
