import json
import sqlite3
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import cast

from apps.api.db.state import connect_state_db


@dataclass(frozen=True)
class AgentRunEvent:
    agent_run_id: str
    seq: int
    event_type: str
    payload: dict[str, object]
    created_at: str


class AgentRunEventOutbox:
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
        self._events_by_run: dict[str, list[AgentRunEvent]] = {}
        self._queue: deque[AgentRunEvent] = deque()
        self._access_by_run: dict[str, set[str]] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    @staticmethod
    def _from_row(row: tuple[object, ...]) -> AgentRunEvent:
        return AgentRunEvent(
            agent_run_id=str(row[0]),
            seq=int(cast(int, row[1])),
            event_type=str(row[2]),
            payload=json.loads(str(row[3])),
            created_at=str(row[4]),
        )

    def append_event(
        self,
        *,
        agent_run_id: str,
        event_type: str,
        payload: dict[str, object],
    ) -> AgentRunEvent:
        if self._connection is None:
            events = self._events_by_run.setdefault(agent_run_id, [])
            seq = events[-1].seq + 1 if events else 1
        else:
            cursor = self._connection.execute(
                """
                select coalesce(max(seq), 0)
                from run_event_record
                where agent_run_id = ?
                """,
                (agent_run_id,),
            )
            row = cursor.fetchone()
            max_seq = 0 if row is None else int(cast(int, row[0]))
            seq = max_seq + 1

        event = AgentRunEvent(
            agent_run_id=agent_run_id,
            seq=seq,
            event_type=event_type,
            payload=payload,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        if self._connection is None:
            events = self._events_by_run.setdefault(agent_run_id, [])
            events.append(event)
            self._queue.append(event)
        else:
            self._connection.execute(
                """
                insert into run_event_record (
                  agent_run_id, seq, event_type, payload_json, created_at
                ) values (?, ?, ?, ?, ?)
                """,
                (
                    event.agent_run_id,
                    event.seq,
                    event.event_type,
                    json.dumps(event.payload, sort_keys=True),
                    event.created_at,
                ),
            )
            self._connection.execute(
                """
                insert into run_event_outbox_record (agent_run_id, seq, published)
                values (?, ?, 0)
                """,
                (event.agent_run_id, event.seq),
            )
            self._connection.commit()
        return event

    def replay(self, *, agent_run_id: str, last_seq: int = 0) -> list[AgentRunEvent]:
        if self._connection is None:
            events = self._events_by_run.get(agent_run_id, [])
            return [event for event in events if event.seq > last_seq]

        cursor = self._connection.execute(
            """
            select agent_run_id, seq, event_type, payload_json, created_at
            from run_event_record
            where agent_run_id = ? and seq > ?
            order by seq asc
            """,
            (agent_run_id, last_seq),
        )
        rows = cursor.fetchall()
        return [self._from_row(row) for row in rows]

    def drain_outbox(self, *, max_items: int = 100) -> list[AgentRunEvent]:
        if self._connection is None:
            drained: list[AgentRunEvent] = []
            while self._queue and len(drained) < max_items:
                drained.append(self._queue.popleft())
            return drained

        cursor = self._connection.execute(
            """
            select re.agent_run_id, re.seq, re.event_type, re.payload_json, re.created_at
            from run_event_outbox_record ro
            join run_event_record re
              on ro.agent_run_id = re.agent_run_id and ro.seq = re.seq
            where ro.published = 0
            order by re.created_at asc
            limit ?
            """,
            (max_items,),
        )
        rows = cursor.fetchall()
        drained = [self._from_row(row) for row in rows]
        for event in drained:
            self._connection.execute(
                """
                update run_event_outbox_record
                set published = 1
                where agent_run_id = ? and seq = ?
                """,
                (event.agent_run_id, event.seq),
            )
        self._connection.commit()
        return drained

    def register_run_access(self, *, agent_run_id: str, workspace_id: str, actor_id: str) -> None:
        if self._connection is None:
            actors = self._access_by_run.setdefault(agent_run_id, set())
            actors.add(actor_id)
            return

        self._connection.execute(
            """
            insert or ignore into run_access_record (agent_run_id, workspace_id, actor_id)
            values (?, ?, ?)
            """,
            (agent_run_id, workspace_id, actor_id),
        )
        self._connection.commit()

    def is_run_access_allowed(self, *, agent_run_id: str, actor_id: str) -> bool | None:
        if self._connection is None:
            actors = self._access_by_run.get(agent_run_id)
            if actors is None:
                return None
            return actor_id in actors

        actor_cursor = self._connection.execute(
            """
            select 1
            from run_access_record
            where agent_run_id = ? and actor_id = ?
            limit 1
            """,
            (agent_run_id, actor_id),
        )
        if actor_cursor.fetchone() is not None:
            return True

        any_cursor = self._connection.execute(
            """
            select 1
            from run_access_record
            where agent_run_id = ?
            limit 1
            """,
            (agent_run_id,),
        )
        if any_cursor.fetchone() is not None:
            return False
        return None
