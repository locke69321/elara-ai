import os
import tempfile
import unittest
from unittest.mock import patch

from apps.api.agents import (
    ActorContext,
    AgentRuntime,
    PolicyEngine,
    SpecialistAgent,
    StubCompletionClient,
)
from apps.api.audit import ImmutableAuditLog
from apps.api.events.outbox import AgentRunEventOutbox
from apps.api.memory import PostgresMemoryStore, SqliteMemoryStore
from apps.api.safety import ApprovalRequiredError, ApprovalService


class RuntimeIntegrationTest(unittest.IsolatedAsyncioTestCase):
    async def test_sqlite_and_postgres_adapter_conformance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sqlite_store = SqliteMemoryStore(
                database_path=os.path.join(tmp_dir, "sqlite-int.sqlite3")
            )
            postgres_store = PostgresMemoryStore(
                database_path=os.path.join(tmp_dir, "postgres-int.sqlite3")
            )

            for store in (sqlite_store, postgres_store):
                await store.upsert_memory(
                    workspace_id="ws-int-adapter",
                    agent_id="agent-int-adapter",
                    memory_id="m-1",
                    content="release approval replay",
                )
                await store.upsert_memory(
                    workspace_id="ws-int-adapter",
                    agent_id="agent-int-adapter",
                    memory_id="m-2",
                    content="release replay",
                )

            sqlite_results = await sqlite_store.search(
                workspace_id="ws-int-adapter",
                agent_id="agent-int-adapter",
                query="release replay",
                top_k=2,
            )
            postgres_results = await postgres_store.search(
                workspace_id="ws-int-adapter",
                agent_id="agent-int-adapter",
                query="release replay",
                top_k=2,
            )

            self.assertEqual(
                [match.memory_id for match in sqlite_results],
                [match.memory_id for match in postgres_results],
            )

    async def test_services_are_repository_backed_across_runtime_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "phase5-runtime.sqlite3")
            with patch.dict(os.environ, {"ELARA_STATE_DB_PATH": db_path}, clear=False):
                first_runtime = AgentRuntime(
                    memory_store=SqliteMemoryStore(database_path=db_path),
                    policy_engine=PolicyEngine(),
                    outbox=AgentRunEventOutbox(database_path=db_path),
                    completion_client=StubCompletionClient(),
                    approval_service=ApprovalService(database_path=db_path),
                    audit_log=ImmutableAuditLog(database_path=db_path),
                )

                owner = ActorContext(user_id="owner-int-restart", role="owner")
                first_runtime.upsert_specialist(
                    workspace_id="ws-int-restart",
                    actor=owner,
                    specialist=SpecialistAgent(
                        id="spec-int-restart",
                        name="Durable Integrator",
                        prompt="Integrate and persist",
                        soul="Methodical",
                        capabilities={"delegate", "write_memory"},
                    ),
                )

                first_execution = await first_runtime.execute_goal(
                    workspace_id="ws-int-restart",
                    actor=owner,
                    goal="persist runtime events",
                )
                replay_before_restart = first_runtime.replay_events(
                    agent_run_id=first_execution.agent_run_id,
                    actor=owner,
                    last_seq=0,
                )
                self.assertGreaterEqual(len(replay_before_restart), 3)

                second_runtime = AgentRuntime(
                    memory_store=SqliteMemoryStore(database_path=db_path),
                    policy_engine=PolicyEngine(),
                    outbox=AgentRunEventOutbox(database_path=db_path),
                    completion_client=StubCompletionClient(),
                    approval_service=ApprovalService(database_path=db_path),
                    audit_log=ImmutableAuditLog(database_path=db_path),
                )

                replay_after_restart = second_runtime.replay_events(
                    agent_run_id=first_execution.agent_run_id,
                    actor=owner,
                    last_seq=1,
                )
                self.assertGreaterEqual(len(replay_after_restart), 1)
                self.assertGreaterEqual(replay_after_restart[0]["seq"], 2)

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

        replay_all = runtime.replay_events(
            agent_run_id=execution.agent_run_id,
            actor=owner,
            last_seq=0,
        )
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

    async def test_replay_events_denies_cross_actor_access(self) -> None:
        runtime = AgentRuntime(
            memory_store=SqliteMemoryStore(),
            policy_engine=PolicyEngine(),
            outbox=AgentRunEventOutbox(),
            completion_client=StubCompletionClient(),
            approval_service=ApprovalService(),
            audit_log=ImmutableAuditLog(),
        )

        owner = ActorContext(user_id="owner-int", role="owner")
        intruder = ActorContext(user_id="intruder-int", role="member")

        await runtime.companion_message(
            workspace_id="ws-int",
            actor_id=owner.user_id,
            message="private memory",
        )

        allowed_events = runtime.replay_events(
            agent_run_id="companion-ws-int",
            actor=owner,
            last_seq=0,
        )
        self.assertGreaterEqual(len(allowed_events), 1)

        with self.assertRaises(PermissionError):
            runtime.replay_events(
                agent_run_id="companion-ws-int",
                actor=intruder,
                last_seq=0,
            )

    async def test_replay_events_denies_legacy_run_without_acl_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "runtime-legacy-replay.sqlite3")
            seeded_outbox = AgentRunEventOutbox(database_path=db_path)
            seeded_outbox.append_event(
                agent_run_id="run-legacy-int",
                event_type="run.started",
                payload={"goal": "legacy replay"},
            )

            runtime = AgentRuntime(
                memory_store=SqliteMemoryStore(database_path=db_path),
                policy_engine=PolicyEngine(),
                outbox=AgentRunEventOutbox(database_path=db_path),
                completion_client=StubCompletionClient(),
                approval_service=ApprovalService(database_path=db_path),
                audit_log=ImmutableAuditLog(database_path=db_path),
            )
            actor = ActorContext(user_id="owner-int", role="owner")

            with self.assertRaises(PermissionError):
                runtime.replay_events(
                    agent_run_id="run-legacy-int",
                    actor=actor,
                    last_seq=0,
                )

    async def test_member_cannot_request_high_impact_delegation_approval(self) -> None:
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
        member = ActorContext(user_id="member-int", role="member")

        runtime.upsert_specialist(
            workspace_id="ws-int-member-risk",
            actor=owner,
            specialist=SpecialistAgent(
                id="spec-risk",
                name="Risk Specialist",
                prompt="Perform risky action",
                soul="Cautious",
                capabilities={"delegate", "external_action"},
            ),
        )

        with self.assertRaises(PermissionError):
            await runtime.execute_goal(
                workspace_id="ws-int-member-risk",
                actor=member,
                goal="run external action",
            )


if __name__ == "__main__":
    unittest.main()
