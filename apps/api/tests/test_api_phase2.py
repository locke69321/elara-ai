import unittest

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
            )
            self.assertEqual(replay_response.status_code, 200)
            replay_payload = replay_response.json()
            self.assertGreaterEqual(len(replay_payload), 1)
            self.assertEqual(replay_payload[0]["seq"], 2)

            listed = client.get("/workspaces/ws-2/specialists")
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
            response = client.get("/agent-runs/missing/events", params={"last_seq": -1})
            self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
