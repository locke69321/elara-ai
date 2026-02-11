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
from apps.api.safety import ApprovalRequiredError, ApprovalService


class RuntimeIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_runtime_integrates_policy_memory_and_outbox(self) -> None:
        approvals = ApprovalService()
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=approvals,
            audit_log=ImmutableAuditLog(),
        )

        owner = ActorContext(user_id="owner-int", role="owner")
        runtime.upsert_specialist(
            workspace_id="ws-int",
            actor=owner,
            specialist=SpecialistAgent(
                id="spec-int",
                name="Integrator",
                prompt="Integrate findings",
                soul="Methodical",
                capabilities={"delegate", "write_memory"},
            ),
        )

        companion = await runtime.companion_message(
            workspace_id="ws-int",
            actor_id="owner-int",
            message="remember this issue",
        )
        self.assertGreaterEqual(len(companion.memory_hits), 1)

        execution = await runtime.execute_goal(
            workspace_id="ws-int",
            actor=owner,
            goal="prepare integration report",
        )
        self.assertEqual(len(execution.delegated_results), 1)

        replay_all = runtime.replay_events(agent_run_id=execution.agent_run_id, last_seq=0)
        self.assertEqual(replay_all[0]["event_type"], "run.started")
        self.assertEqual(replay_all[-1]["event_type"], "run.completed")

    async def test_high_impact_delegation_requires_approval_then_succeeds(self) -> None:
        approvals = ApprovalService()
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=approvals,
            audit_log=ImmutableAuditLog(),
        )

        owner = ActorContext(user_id="owner-int", role="owner")
        runtime.upsert_specialist(
            workspace_id="ws-int",
            actor=owner,
            specialist=SpecialistAgent(
                id="spec-risk",
                name="Risk Specialist",
                prompt="Perform risky action",
                soul="Cautious",
                capabilities={"delegate", "external_action"},
            ),
        )

        with self.assertRaises(ApprovalRequiredError) as context:
            await runtime.execute_goal(
                workspace_id="ws-int",
                actor=owner,
                goal="run external action",
            )

        approval_id = context.exception.approval_id
        decided = approvals.decide_request(
            approval_id=approval_id,
            approver_id="owner-int",
            decision="approved",
        )
        self.assertEqual(decided.status, "approved")

        result = await runtime.execute_goal(
            workspace_id="ws-int",
            actor=owner,
            goal="run external action",
            approved_request_ids={approval_id},
        )
        self.assertEqual(len(result.delegated_results), 1)


if __name__ == "__main__":
    unittest.main()
