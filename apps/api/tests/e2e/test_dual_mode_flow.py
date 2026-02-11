import os
import tempfile
import unittest
from hashlib import sha256
from unittest.mock import patch

from fastapi.testclient import TestClient

from apps.api.db.state import connect_state_db
from apps.api.main import app
from apps.api.memory import PostgresMemoryStore, SqliteMemoryStore


class DualModeFlowE2ETest(unittest.TestCase):
    def test_workspace_owner_cannot_be_reclaimed_by_different_owner_after_restart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "phase5-owner-restart.sqlite3")
            with patch.dict(os.environ, {"ELARA_STATE_DB_PATH": db_path}, clear=False):
                with TestClient(app) as first_client:
                    create_specialist = first_client.post(
                        "/workspaces/ws-e2e-owner-restart/specialists",
                        json={
                            "id": "spec-owner-lock",
                            "name": "Owner Lock Specialist",
                            "prompt": "Track ownership",
                            "soul": "Strict",
                            "capabilities": ["delegate"],
                        },
                        headers={"x-user-id": "owner-a", "x-user-role": "owner"},
                    )
                    self.assertEqual(create_specialist.status_code, 201)

                with TestClient(app) as second_client:
                    cross_owner = second_client.get(
                        "/workspaces/ws-e2e-owner-restart/specialists",
                        headers={"x-user-id": "owner-b", "x-user-role": "owner"},
                    )
                    self.assertEqual(cross_owner.status_code, 403)

                    original_owner = second_client.get(
                        "/workspaces/ws-e2e-owner-restart/specialists",
                        headers={"x-user-id": "owner-a", "x-user-role": "owner"},
                    )
                    self.assertEqual(original_owner.status_code, 200)

    def test_restart_persists_invitations_approvals_audit_and_replay(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "phase5-e2e-state.sqlite3")
            with patch.dict(os.environ, {"ELARA_STATE_DB_PATH": db_path}, clear=False):
                with TestClient(app) as first_client:
                    invite_response = first_client.post(
                        "/workspaces/ws-e2e-restart/invitations",
                        json={"email": "persist@example.com"},
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(invite_response.status_code, 201)
                    token = invite_response.json()["token"]

                    accept_response = first_client.post(
                        f"/invitations/{token}/accept",
                        json={"user_id": "member-restart"},
                    )
                    self.assertEqual(accept_response.status_code, 200)

                    approval_response = first_client.post(
                        "/workspaces/ws-e2e-restart/approvals",
                        json={
                            "capability": "run_tool",
                            "action": "delegate:spec:persist",
                            "reason": "persist approval request",
                        },
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(approval_response.status_code, 201)

                    companion_response = first_client.post(
                        "/workspaces/ws-e2e-restart/companion/messages",
                        json={"message": "remember restart persistence context"},
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(companion_response.status_code, 200)
                    self.assertGreaterEqual(len(companion_response.json()["memory_hits"]), 1)

                    create_specialist = first_client.post(
                        "/workspaces/ws-e2e-restart/specialists",
                        json={
                            "id": "spec-restart",
                            "name": "Restart Specialist",
                            "prompt": "Do restart-safe work",
                            "soul": "Durable",
                            "capabilities": ["delegate", "write_memory"],
                        },
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(create_specialist.status_code, 201)

                    execution_response = first_client.post(
                        "/workspaces/ws-e2e-restart/execution/goals",
                        json={"goal": "collect durable replay events"},
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(execution_response.status_code, 200)
                    agent_run_id = execution_response.json()["agent_run_id"]

                with TestClient(app) as second_client:
                    invitations_response = second_client.get(
                        "/workspaces/ws-e2e-restart/invitations",
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(invitations_response.status_code, 200)
                    self.assertEqual(len(invitations_response.json()), 1)

                    approvals_response = second_client.get(
                        "/workspaces/ws-e2e-restart/approvals",
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(approvals_response.status_code, 200)
                    self.assertEqual(len(approvals_response.json()), 1)

                    audit_response = second_client.get(
                        "/workspaces/ws-e2e-restart/audit-events",
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(audit_response.status_code, 200)
                    audit_actions = [event["action"] for event in audit_response.json()]
                    self.assertIn("invitation.created", audit_actions)
                    self.assertIn("invitation.accepted", audit_actions)
                    self.assertIn("goal.execute", audit_actions)

                    replay_response = second_client.get(
                        f"/agent-runs/{agent_run_id}/events",
                        params={"last_seq": 2},
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(replay_response.status_code, 200)
                    replay_events = replay_response.json()
                    self.assertGreaterEqual(len(replay_events), 1)
                    self.assertGreaterEqual(replay_events[0]["seq"], 3)

                    companion_after_restart = second_client.post(
                        "/workspaces/ws-e2e-restart/companion/messages",
                        json={"message": "restart persistence"},
                        headers={"x-user-id": "owner-restart", "x-user-role": "owner"},
                    )
                    self.assertEqual(companion_after_restart.status_code, 200)
                    self.assertGreaterEqual(
                        len(companion_after_restart.json()["memory_hits"]),
                        1,
                    )

                    member_after_restart = second_client.post(
                        "/workspaces/ws-e2e-restart/companion/messages",
                        json={"message": "member restart persistence"},
                        headers={"x-user-id": "member-restart", "x-user-role": "member"},
                    )
                    self.assertEqual(member_after_restart.status_code, 200)

    def test_owner_can_run_end_to_end_dual_mode_flow(self) -> None:
        with TestClient(app) as client:
            create_specialist = client.post(
                "/workspaces/ws-e2e/specialists",
                json={
                    "id": "spec-e2e",
                    "name": "Research Specialist",
                    "prompt": "Research and summarize",
                    "soul": "Focused",
                    "capabilities": ["delegate", "write_memory"],
                },
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(create_specialist.status_code, 201)

            companion_reply = client.post(
                "/workspaces/ws-e2e/companion/messages",
                json={"message": "remember release planning context"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(companion_reply.status_code, 200)
            self.assertIn("memory_hits", companion_reply.json())

            execution_reply = client.post(
                "/workspaces/ws-e2e/execution/goals",
                json={"goal": "build release summary"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(execution_reply.status_code, 200)
            execution_payload = execution_reply.json()
            self.assertEqual(len(execution_payload["delegated_results"]), 1)

            replay = client.get(
                f"/agent-runs/{execution_payload['agent_run_id']}/events",
                params={"last_seq": 1},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(replay.status_code, 200)
            self.assertGreaterEqual(len(replay.json()), 1)

    def test_member_cannot_edit_specialists_e2e(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-e2e-auth/specialists",
                json={
                    "id": "spec-locked",
                    "name": "Locked Specialist",
                    "prompt": "Do work",
                    "soul": "Strict",
                    "capabilities": ["delegate"],
                },
                headers={"x-user-id": "member-e2e", "x-user-role": "member"},
            )
            self.assertEqual(response.status_code, 403)

    def test_list_specialists_requires_identity_headers_e2e(self) -> None:
        with TestClient(app) as client:
            create = client.post(
                "/workspaces/ws-e2e-specialists/specialists",
                json={
                    "id": "spec-list-auth",
                    "name": "List Auth Specialist",
                    "prompt": "Do work",
                    "soul": "Strict",
                    "capabilities": ["delegate"],
                },
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(create.status_code, 201)

            listed = client.get("/workspaces/ws-e2e-specialists/specialists")
            self.assertEqual(listed.status_code, 401)

    def test_privileged_route_rejects_missing_identity_headers_e2e(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-e2e-missing-auth/specialists",
                json={
                    "id": "spec-unauth",
                    "name": "Unauth Specialist",
                    "prompt": "Do work",
                    "soul": "Strict",
                    "capabilities": ["delegate"],
                },
            )
            self.assertEqual(response.status_code, 401)

    def test_high_impact_execution_requires_approval_and_can_resume(self) -> None:
        with TestClient(app) as client:
            create_specialist = client.post(
                "/workspaces/ws-e2e-approval/specialists",
                json={
                    "id": "spec-high-impact",
                    "name": "High Impact Specialist",
                    "prompt": "Perform external action",
                    "soul": "Careful",
                    "capabilities": ["delegate", "external_action"],
                },
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(create_specialist.status_code, 201)

            first_execute = client.post(
                "/workspaces/ws-e2e-approval/execution/goals",
                json={"goal": "perform high impact action"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(first_execute.status_code, 409)
            approval_id = first_execute.json()["detail"]["approval_id"]

            decide = client.post(
                f"/approvals/{approval_id}/decision",
                json={"decision": "approved"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(decide.status_code, 200)

            second_execute = client.post(
                "/workspaces/ws-e2e-approval/execution/goals",
                json={
                    "goal": "perform high impact action",
                    "approved_request_ids": [approval_id],
                },
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(second_execute.status_code, 200)
            self.assertEqual(len(second_execute.json()["delegated_results"]), 1)

    def test_member_cannot_execute_high_impact_goal_e2e(self) -> None:
        with TestClient(app) as client:
            create_invitation = client.post(
                "/workspaces/ws-e2e-member-risk/invitations",
                json={"email": "member-risk@example.com"},
                headers={"x-user-id": "owner-e2e-risk", "x-user-role": "owner"},
            )
            self.assertEqual(create_invitation.status_code, 201)
            token = create_invitation.json()["token"]

            accept_invitation = client.post(
                f"/invitations/{token}/accept",
                json={"user_id": "member-e2e-risk"},
            )
            self.assertEqual(accept_invitation.status_code, 200)

            create_specialist = client.post(
                "/workspaces/ws-e2e-member-risk/specialists",
                json={
                    "id": "spec-member-risk",
                    "name": "Member Risk Specialist",
                    "prompt": "Perform external action",
                    "soul": "Cautious",
                    "capabilities": ["delegate", "external_action"],
                },
                headers={"x-user-id": "owner-e2e-risk", "x-user-role": "owner"},
            )
            self.assertEqual(create_specialist.status_code, 201)

            member_execute = client.post(
                "/workspaces/ws-e2e-member-risk/execution/goals",
                json={"goal": "perform high impact action"},
                headers={"x-user-id": "member-e2e-risk", "x-user-role": "member"},
            )
            self.assertEqual(member_execute.status_code, 403)
            self.assertIn(
                "high-impact",
                member_execute.json()["detail"],
            )

    def test_invitation_flow_and_audit_log_e2e(self) -> None:
        with TestClient(app) as client:
            create_invitation = client.post(
                "/workspaces/ws-e2e-invite/invitations",
                json={"email": "invitee@example.com"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(create_invitation.status_code, 201)
            token = create_invitation.json()["token"]

            accept_invitation = client.post(
                f"/invitations/{token}/accept",
                json={"user_id": "member-e2e"},
            )
            self.assertEqual(accept_invitation.status_code, 200)

            audit_events = client.get(
                "/workspaces/ws-e2e-invite/audit-events",
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(audit_events.status_code, 200)
            audit_payload = audit_events.json()
            actions = [event["action"] for event in audit_payload]
            self.assertIn("invitation.created", actions)
            self.assertIn("invitation.accepted", actions)

            expected_fingerprint = sha256(token.encode("utf-8")).hexdigest()[:12]
            created_event = next(
                event for event in audit_payload if event["action"] == "invitation.created"
            )
            accepted_event = next(
                event for event in audit_payload if event["action"] == "invitation.accepted"
            )
            self.assertNotIn("token", created_event["metadata"])
            self.assertNotIn("token", accepted_event["metadata"])
            self.assertEqual(
                created_event["metadata"]["token_fingerprint"],
                expected_fingerprint,
            )
            self.assertEqual(
                accepted_event["metadata"]["token_fingerprint"],
                expected_fingerprint,
            )

    def test_replay_requires_authenticated_actor_and_denies_cross_actor_access(self) -> None:
        with TestClient(app) as client:
            companion_reply = client.post(
                "/workspaces/ws-e2e-replay/companion/messages",
                json={"message": "remember private details"},
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(companion_reply.status_code, 200)

            unauthenticated_replay = client.get("/agent-runs/companion-ws-e2e-replay/events")
            self.assertEqual(unauthenticated_replay.status_code, 401)

            cross_actor_replay = client.get(
                "/agent-runs/companion-ws-e2e-replay/events",
                headers={"x-user-id": "intruder-e2e", "x-user-role": "member"},
            )
            self.assertEqual(cross_actor_replay.status_code, 403)

            owner_replay = client.get(
                "/agent-runs/companion-ws-e2e-replay/events",
                headers={"x-user-id": "owner-e2e", "x-user-role": "owner"},
            )
            self.assertEqual(owner_replay.status_code, 200)
            self.assertGreaterEqual(len(owner_replay.json()), 1)

    def test_replay_denies_legacy_run_without_acl_rows_e2e(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "phase5-replay-legacy.sqlite3")
            state_connection = connect_state_db(db_path)
            try:
                state_connection.execute(
                    """
                    insert into run_event_record (
                      agent_run_id, seq, event_type, payload_json, created_at
                    ) values (?, ?, ?, ?, ?)
                    """,
                    (
                        "run-legacy-no-acl",
                        1,
                        "run.started",
                        '{"goal":"legacy replay"}',
                        "2026-02-11T00:00:00+00:00",
                    ),
                )
                state_connection.execute(
                    """
                    insert into run_event_outbox_record (agent_run_id, seq, published)
                    values (?, ?, 1)
                    """,
                    ("run-legacy-no-acl", 1),
                )
                state_connection.commit()
            finally:
                state_connection.close()

            with patch.dict(os.environ, {"ELARA_STATE_DB_PATH": db_path}, clear=False):
                with TestClient(app) as client:
                    replay = client.get(
                        "/agent-runs/run-legacy-no-acl/events",
                        headers={"x-user-id": "intruder-e2e", "x-user-role": "member"},
                    )
                    self.assertEqual(replay.status_code, 403)

    def test_cross_workspace_owner_cannot_decide_foreign_approval_e2e(self) -> None:
        with TestClient(app) as client:
            create_ws_a = client.post(
                "/workspaces/ws-e2e-approval-a/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec-a:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_ws_a.status_code, 201)
            approval_id = create_ws_a.json()["id"]

            create_ws_b = client.post(
                "/workspaces/ws-e2e-approval-b/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec-b:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(create_ws_b.status_code, 201)

            cross_decide = client.post(
                f"/approvals/{approval_id}/decision",
                json={"decision": "approved"},
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(cross_decide.status_code, 403)

    def test_cross_workspace_owner_cannot_read_foreign_workspace_records_e2e(self) -> None:
        with TestClient(app) as client:
            create_specialist = client.post(
                "/workspaces/ws-e2e-tenant-a/specialists",
                json={
                    "id": "spec-tenant-a",
                    "name": "Tenant A Specialist",
                    "prompt": "Do work",
                    "soul": "Strict",
                    "capabilities": ["delegate"],
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_specialist.status_code, 201)

            create_invitation = client.post(
                "/workspaces/ws-e2e-tenant-a/invitations",
                json={"email": "invitee@example.com"},
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_invitation.status_code, 201)

            create_approval = client.post(
                "/workspaces/ws-e2e-tenant-a/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_approval.status_code, 201)

            foreign_specialists = client.get(
                "/workspaces/ws-e2e-tenant-a/specialists",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_specialists.status_code, 403)

            foreign_invitations = client.get(
                "/workspaces/ws-e2e-tenant-a/invitations",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_invitations.status_code, 403)

            foreign_approvals = client.get(
                "/workspaces/ws-e2e-tenant-a/approvals",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_approvals.status_code, 403)

            foreign_audit = client.get(
                "/workspaces/ws-e2e-tenant-a/audit-events",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_audit.status_code, 403)


class MemoryAdapterE2ETest(unittest.IsolatedAsyncioTestCase):
    async def test_cross_backend_memory_retrieval_parity_and_isolation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            sqlite_store = SqliteMemoryStore(
                database_path=os.path.join(tmp_dir, "sqlite-e2e.sqlite3")
            )
            postgres_store = PostgresMemoryStore(
                database_path=os.path.join(tmp_dir, "postgres-e2e.sqlite3")
            )

            for store in (sqlite_store, postgres_store):
                await store.upsert_memory(
                    workspace_id="ws-e2e-parity",
                    agent_id="agent-e2e",
                    memory_id="m-visible",
                    content="approval timeline replay",
                )
                await store.upsert_memory(
                    workspace_id="ws-e2e-hidden",
                    agent_id="agent-e2e",
                    memory_id="m-hidden",
                    content="approval timeline replay",
                )

            sqlite_matches = await sqlite_store.search(
                workspace_id="ws-e2e-parity",
                agent_id="agent-e2e",
                query="approval timeline",
            )
            postgres_matches = await postgres_store.search(
                workspace_id="ws-e2e-parity",
                agent_id="agent-e2e",
                query="approval timeline",
            )

            self.assertEqual(
                [match.memory_id for match in sqlite_matches],
                [match.memory_id for match in postgres_matches],
            )
            self.assertEqual([match.memory_id for match in sqlite_matches], ["m-visible"])


if __name__ == "__main__":
    unittest.main()
