import unittest

from apps.api.main import app


class MainAppTest(unittest.TestCase):
    def test_core_routes_are_registered(self) -> None:
        registered_routes = {route.path for route in app.router.routes}
        self.assertIn("/health", registered_routes)
        self.assertIn("/workspaces/{workspace_id}/specialists", registered_routes)
        self.assertIn("/workspaces/{workspace_id}/companion/messages", registered_routes)
        self.assertIn("/workspaces/{workspace_id}/execution/goals", registered_routes)
        self.assertIn("/agent-runs/{agent_run_id}/events", registered_routes)


if __name__ == "__main__":
    unittest.main()
