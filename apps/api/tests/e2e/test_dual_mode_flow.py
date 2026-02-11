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


if __name__ == "__main__":
    unittest.main()
