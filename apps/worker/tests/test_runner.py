import unittest

from apps.api.events.outbox import AgentRunEventOutbox
from apps.worker.runner import run_once


class WorkerRunnerTest(unittest.IsolatedAsyncioTestCase):
    async def test_run_once_drains_outbox_records(self) -> None:
        outbox = AgentRunEventOutbox()
        outbox.append_event(agent_run_id="run-worker", event_type="run.started", payload={})
        outbox.append_event(agent_run_id="run-worker", event_type="run.completed", payload={})

        delivered = await run_once(outbox)

        self.assertEqual(delivered, ["run-worker:1", "run-worker:2"])


if __name__ == "__main__":
    unittest.main()
