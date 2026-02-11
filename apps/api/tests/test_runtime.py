import unittest

from apps.api.agents import (
    ActorContext,
    AgentRuntime,
    PolicyEngine,
    SpecialistAgent,
    StubCompletionClient,
)
from apps.api.audit import ImmutableAuditLog
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory import SqliteMemoryStore
from apps.api.safety import ApprovalService


class AgentRuntimeTest(unittest.IsolatedAsyncioTestCase):
    async def test_companion_message_records_memory_and_returns_hits(self) -> None:
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )

        first = await runtime.companion_message(
            workspace_id="ws-1",
            actor_id="owner-1",
            message="remember this detail",
        )
        second = await runtime.companion_message(
            workspace_id="ws-1",
            actor_id="owner-1",
            message="detail",
        )

        self.assertGreaterEqual(len(first.memory_hits), 1)
        self.assertGreaterEqual(len(second.memory_hits), 1)

    async def test_execute_goal_delegates_to_eligible_specialists(self) -> None:
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )
        actor = ActorContext(user_id="owner-1", role="owner")

        runtime.upsert_specialist(
            workspace_id="ws-1",
            actor=actor,
            specialist=SpecialistAgent(
                id="spec-research",
                name="Research Specialist",
                prompt="Do research",
                soul="Analytical",
                capabilities={"delegate", "write_memory"},
            ),
        )

        result = await runtime.execute_goal(
            workspace_id="ws-1",
            actor=actor,
            goal="Summarize release risks",
        )

        self.assertEqual(len(result.delegated_results), 1)
        self.assertIn("delegated", result.summary.lower())

        replay = runtime.replay_events(agent_run_id=result.agent_run_id, last_seq=0)
        self.assertEqual(replay[0]["event_type"], "run.started")
        self.assertEqual(replay[-1]["event_type"], "run.completed")

    async def test_execute_goal_raises_when_no_eligible_specialist_exists(self) -> None:
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )
        actor = ActorContext(user_id="owner-1", role="owner")

        with self.assertRaises(ValueError):
            await runtime.execute_goal(
                workspace_id="ws-empty",
                actor=actor,
                goal="No specialists available",
            )


if __name__ == "__main__":
    unittest.main()
