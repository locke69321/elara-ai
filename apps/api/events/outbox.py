from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class AgentRunEvent:
    agent_run_id: str
    seq: int
    event_type: str
    payload: dict[str, object]
    created_at: str


class AgentRunEventOutbox:
    def __init__(self) -> None:
        self._events_by_run: dict[str, list[AgentRunEvent]] = {}
        self._queue: deque[AgentRunEvent] = deque()

    def append_event(
        self,
        *,
        agent_run_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> AgentRunEvent:
        events = self._events_by_run.setdefault(agent_run_id, [])
        seq = events[-1].seq + 1 if events else 1

        event = AgentRunEvent(
            agent_run_id=agent_run_id,
            seq=seq,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        events.append(event)
        self._queue.append(event)
        return event

    def replay(self, *, agent_run_id: str, last_seq: int = 0) -> list[AgentRunEvent]:
        events = self._events_by_run.get(agent_run_id, [])
        return [event for event in events if event.seq > last_seq]

    def drain_outbox(self, *, max_items: int = 100) -> list[AgentRunEvent]:
        drained: list[AgentRunEvent] = []
        while self._queue and len(drained) < max_items:
            drained.append(self._queue.popleft())
        return drained
