import unittest
from hashlib import sha256

from fastapi.testclient import TestClient

from apps.api.main import app


class Phase2ApiTest(unittest.TestCase):
    def test_health_route_returns_ok(self) -> None:
        with TestClient(app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})

    def test_member_cannot_create_specialist(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-1/specialists",
                json={
                    "id": "spec-a",
                    "name": "Spec A",
                    "prompt": "Do work",
                    "soul": "Calm",
                    "capabilities": ["delegate"],
                },
                headers={"x-user-id": "member-1", "x-user-role": "member"},
            )

            self.assertEqual(response.status_code, 403)

    def test_missing_identity_headers_cannot_create_specialist(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-missing-auth/specialists",
                json={
                    "id": "spec-a",
                    "name": "Spec A",
                    "prompt": "Do work",
                    "soul": "Calm",
                    "capabilities": ["delegate"],
                },
            )
            self.assertEqual(response.status_code, 401)

    def test_owner_can_create_specialist_and_execute_goal(self) -> None:
        with TestClient(app) as client:
            create_response = client.post(
                "/workspaces/ws-2/specialists",
                json={
                    "id": "spec-b",
                    "name": "Spec B",
                    "prompt": "Do work",
                    "soul": "Precise",
                    "capabilities": ["delegate", "write_memory"],
                },
                headers={"x-user-id": "owner-1", "x-user-role": "owner"},
            )
            self.assertEqual(create_response.status_code, 201)

            execute_response = client.post(
                "/workspaces/ws-2/execution/goals",
                json={"goal": "Prepare a status summary"},
                headers={"x-user-id": "owner-1", "x-user-role": "owner"},
            )
            self.assertEqual(execute_response.status_code, 200)
            payload = execute_response.json()
            self.assertEqual(len(payload["delegated_results"]), 1)

            replay_response = client.get(
                f"/agent-runs/{payload['agent_run_id']}/events",
                params={"last_seq": 1},
                headers={"x-user-id": "owner-1", "x-user-role": "owner"},
            )
            self.assertEqual(replay_response.status_code, 200)
            replay_payload = replay_response.json()
            self.assertGreaterEqual(len(replay_payload), 1)
            self.assertEqual(replay_payload[0]["seq"], 2)

            listed = client.get(
                "/workspaces/ws-2/specialists",
                headers={"x-user-id": "owner-1", "x-user-role": "owner"},
            )
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(len(listed.json()), 1)

    def test_companion_message_round_trip(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-3/companion/messages",
                json={"message": "hello companion"},
                headers={"x-user-id": "owner-3", "x-user-role": "owner"},
            )
            self.assertEqual(response.status_code, 200)
            payload = response.json()
            self.assertIn("response", payload)
            self.assertIn("memory_hits", payload)

    def test_invalid_role_header_returns_400(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-4/companion/messages",
                json={"message": "hello"},
                headers={"x-user-id": "u1", "x-user-role": "invalid"},
            )
            self.assertEqual(response.status_code, 400)

    def test_execute_goal_without_specialists_returns_400(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-5/execution/goals",
                json={"goal": "goal with no specialists"},
                headers={"x-user-id": "owner-5", "x-user-role": "owner"},
            )
            self.assertEqual(response.status_code, 400)

    def test_event_replay_negative_last_seq_returns_400(self) -> None:
        with TestClient(app) as client:
            response = client.get(
                "/agent-runs/missing/events",
                params={"last_seq": -1},
                headers={"x-user-id": "owner-1", "x-user-role": "owner"},
            )
            self.assertEqual(response.status_code, 400)

    def test_owner_can_create_and_list_invitations(self) -> None:
        with TestClient(app) as client:
            create = client.post(
                "/workspaces/ws-invite/invitations",
                json={"email": "new-user@example.com"},
                headers={"x-user-id": "owner-invite", "x-user-role": "owner"},
            )
            self.assertEqual(create.status_code, 201)

            listed = client.get(
                "/workspaces/ws-invite/invitations",
                headers={"x-user-id": "owner-invite", "x-user-role": "owner"},
            )
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(len(listed.json()), 1)

    def test_member_cannot_create_invitation(self) -> None:
        with TestClient(app) as client:
            response = client.post(
                "/workspaces/ws-invite/invitations",
                json={"email": "new-user@example.com"},
                headers={"x-user-id": "member-invite", "x-user-role": "member"},
            )
            self.assertEqual(response.status_code, 403)

    def test_cross_workspace_owner_cannot_list_foreign_records(self) -> None:
        with TestClient(app) as client:
            create_invitation = client.post(
                "/workspaces/ws-tenant-invite/invitations",
                json={"email": "new-user@example.com"},
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_invitation.status_code, 201)

            create_approval = client.post(
                "/workspaces/ws-tenant-invite/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_approval.status_code, 201)

            foreign_invitations = client.get(
                "/workspaces/ws-tenant-invite/invitations",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_invitations.status_code, 403)

            foreign_approvals = client.get(
                "/workspaces/ws-tenant-invite/approvals",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_approvals.status_code, 403)

            foreign_audit = client.get(
                "/workspaces/ws-tenant-invite/audit-events",
                headers={"x-user-id": "owner-b", "x-user-role": "owner"},
            )
            self.assertEqual(foreign_audit.status_code, 403)

    def test_invitation_audit_metadata_redacts_raw_token(self) -> None:
        with TestClient(app) as client:
            create = client.post(
                "/workspaces/ws-invite-audit/invitations",
                json={"email": "new-user@example.com"},
                headers={"x-user-id": "owner-invite", "x-user-role": "owner"},
            )
            self.assertEqual(create.status_code, 201)
            token = create.json()["token"]
            expected_fingerprint = sha256(token.encode("utf-8")).hexdigest()[:12]

            accepted = client.post(
                f"/invitations/{token}/accept",
                json={"user_id": "member-invite"},
            )
            self.assertEqual(accepted.status_code, 200)

            audit_events = client.get(
                "/workspaces/ws-invite-audit/audit-events",
                headers={"x-user-id": "owner-invite", "x-user-role": "owner"},
            )
            self.assertEqual(audit_events.status_code, 200)

            created_event = next(
                event
                for event in audit_events.json()
                if event["action"] == "invitation.created"
            )
            accepted_event = next(
                event
                for event in audit_events.json()
                if event["action"] == "invitation.accepted"
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

    def test_owner_can_create_and_decide_approval(self) -> None:
        with TestClient(app) as client:
            create = client.post(
                "/workspaces/ws-approval/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-approval", "x-user-role": "owner"},
            )
            self.assertEqual(create.status_code, 201)
            approval_id = create.json()["id"]

            decide = client.post(
                f"/approvals/{approval_id}/decision",
                json={"decision": "approved"},
                headers={"x-user-id": "owner-approval", "x-user-role": "owner"},
            )
            self.assertEqual(decide.status_code, 200)
            self.assertEqual(decide.json()["status"], "approved")

            listed = client.get(
                "/workspaces/ws-approval/approvals",
                headers={"x-user-id": "owner-approval", "x-user-role": "owner"},
            )
            self.assertEqual(listed.status_code, 200)
            self.assertEqual(len(listed.json()), 1)

    def test_owner_cannot_decide_other_owners_approval_request(self) -> None:
        with TestClient(app) as client:
            create_ws_a = client.post(
                "/workspaces/ws-approval-a/approvals",
                json={
                    "capability": "run_tool",
                    "action": "delegate:spec-a:goal",
                    "reason": "confirm risky operation",
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create_ws_a.status_code, 201)
            approval_id = create_ws_a.json()["id"]

            # Seed a separate workspace request for owner-b to model a different tenant owner.
            create_ws_b = client.post(
                "/workspaces/ws-approval-b/approvals",
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


if __name__ == "__main__":
    unittest.main()
