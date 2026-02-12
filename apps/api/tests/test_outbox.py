import os
import tempfile
import unittest

from apps.api.events.outbox import AgentRunEventOutbox


class AgentRunEventOutboxTest(unittest.TestCase):
    def test_sequence_and_replay_cursor_persist_across_outbox_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "outbox.sqlite3")
            first = AgentRunEventOutbox(database_path=db_path)
            first.append_event(agent_run_id="run-persist", event_type="a", payload={})
            first.append_event(agent_run_id="run-persist", event_type="b", payload={})

            second = AgentRunEventOutbox(database_path=db_path)
            second.append_event(agent_run_id="run-persist", event_type="c", payload={})

            replayed = second.replay(agent_run_id="run-persist", last_seq=1)
            self.assertEqual([event.seq for event in replayed], [2, 3])

    def test_append_assigns_monotonic_sequence(self) -> None:
        outbox = AgentRunEventOutbox()

        event_a = outbox.append_event(
            agent_run_id="run-1",
            event_type="task.started",
            payload={"task": "A"},
        )
        event_b = outbox.append_event(
            agent_run_id="run-1",
            event_type="task.completed",
            payload={"task": "A"},
        )

        self.assertEqual(event_a.seq, 1)
        self.assertEqual(event_b.seq, 2)

    def test_replay_resumes_from_last_sequence(self) -> None:
        outbox = AgentRunEventOutbox()

        outbox.append_event(agent_run_id="run-2", event_type="a", payload={})
        outbox.append_event(agent_run_id="run-2", event_type="b", payload={})
        outbox.append_event(agent_run_id="run-2", event_type="c", payload={})

        replayed = outbox.replay(agent_run_id="run-2", last_seq=1)

        self.assertEqual([event.seq for event in replayed], [2, 3])

    def test_drain_outbox_respects_max_items(self) -> None:
        outbox = AgentRunEventOutbox()
        outbox.append_event(agent_run_id="run-3", event_type="a", payload={})
        outbox.append_event(agent_run_id="run-3", event_type="b", payload={})

        drained_once = outbox.drain_outbox(max_items=1)
        drained_twice = outbox.drain_outbox(max_items=10)

        self.assertEqual(len(drained_once), 1)
        self.assertEqual(len(drained_twice), 1)


if __name__ == "__main__":
    unittest.main()
