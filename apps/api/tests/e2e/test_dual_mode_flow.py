import unittest

from fastapi.testclient import TestClient

from apps.api.main import app


class DualModeFlowE2ETest(unittest.TestCase):
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
            actions = [event["action"] for event in audit_events.json()]
            self.assertIn("invitation.created", actions)
            self.assertIn("invitation.accepted", actions)

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


if __name__ == "__main__":
    unittest.main()
