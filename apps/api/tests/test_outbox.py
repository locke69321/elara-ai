import unittest

from apps.api.events.outbox import AgentRunEventOutbox


class AgentRunEventOutboxTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
