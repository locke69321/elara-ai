import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from apps.api.agents import ActorContext, AgentRuntime, PolicyEngine, SpecialistAgent
from apps.api.audit import ImmutableAuditLog
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory import SqliteMemoryStore
from apps.api.safety import ApprovalService


class RuntimeUnitTest(unittest.IsolatedAsyncioTestCase):
    async def test_companion_message_uses_completion_client(self) -> None:
        complete_mock = AsyncMock(return_value="mocked-companion")
        completion_client = SimpleNamespace(complete=complete_mock)

        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=completion_client,
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )

        await runtime.companion_message(
            workspace_id="ws-unit",
            actor_id="owner-unit",
            message="hello",
        )

        complete_mock.assert_awaited_once_with(
            system_prompt="companion_primary",
            user_input="hello",
        )

    async def test_execute_goal_uses_completion_client_per_delegation(self) -> None:
        complete_mock = AsyncMock(return_value="mocked-specialist-output")
        completion_client = SimpleNamespace(complete=complete_mock)

        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=completion_client,
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )
        actor = ActorContext(user_id="owner-unit", role="owner")

        runtime.upsert_specialist(
            workspace_id="ws-unit",
            actor=actor,
            specialist=SpecialistAgent(
                id="spec-unit",
                name="Unit Specialist",
                prompt="Handle unit task",
                soul="Precise",
                capabilities={"delegate", "write_memory"},
            ),
        )

        result = await runtime.execute_goal(
            workspace_id="ws-unit",
            actor=actor,
            goal="unit goal",
        )

        self.assertEqual(len(result.delegated_results), 1)
        complete_mock.assert_awaited_with(
            system_prompt="Handle unit task | soul=Precise",
            user_input="Subtask 1: contribute to goal 'unit goal'",
        )

    async def test_companion_replay_payload_redacts_sensitive_identifiers(self) -> None:
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=SimpleNamespace(complete=AsyncMock(return_value="ok")),
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )
        actor = ActorContext(user_id="owner-unit", role="owner")

        await runtime.companion_message(
            workspace_id="ws-unit",
            actor_id=actor.user_id,
            message="remember secret",
        )

        events = runtime.replay_events(
            agent_run_id="companion-ws-unit",
            actor=actor,
            last_seq=0,
        )
        self.assertEqual(events[0]["event_type"], "companion.message")
        payload = events[0]["payload"]
        self.assertNotIn("actor_id", payload)
        self.assertNotIn("memory_hits", payload)
        self.assertIn("memory_hit_count", payload)


if __name__ == "__main__":
    unittest.main()
