import unittest

from apps.api.main import app


class MainAppTest(unittest.TestCase):
    def test_health_route_is_registered(self) -> None:
        registered_routes = {route.path for route in app.router.routes}
        self.assertIn("/health", registered_routes)


if __name__ == "__main__":
    unittest.main()
