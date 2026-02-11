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


if __name__ == "__main__":
    unittest.main()
