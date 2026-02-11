import unittest

from fastapi.testclient import TestClient

from apps.api.main import app


class AppAuthzIntegrationTest(unittest.TestCase):
    def test_cross_workspace_reads_are_blocked(self) -> None:
        with TestClient(app) as client:
            create = client.post(
                "/workspaces/ws-authz-a/specialists",
                json={
                    "id": "spec-authz",
                    "name": "Authz Specialist",
                    "prompt": "Keep data scoped",
                    "soul": "Strict",
                    "capabilities": ["delegate"],
                },
                headers={"x-user-id": "owner-a", "x-user-role": "owner"},
            )
            self.assertEqual(create.status_code, 201)

            for path in (
                "/workspaces/ws-authz-a/specialists",
                "/workspaces/ws-authz-a/invitations",
                "/workspaces/ws-authz-a/approvals",
                "/workspaces/ws-authz-a/audit-events",
            ):
                response = client.get(
                    path,
                    headers={"x-user-id": "owner-b", "x-user-role": "owner"},
                )
                self.assertEqual(response.status_code, 403, path)


if __name__ == "__main__":
    unittest.main()
