import unittest
from types import SimpleNamespace

from fastapi import HTTPException

from apps.api.main import get_runtime


class RuntimeDependencyTest(unittest.TestCase):
    def test_get_runtime_raises_when_runtime_missing(self) -> None:
        request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace()))

        with self.assertRaises(HTTPException) as context:
            get_runtime(request)

        self.assertEqual(context.exception.status_code, 503)


if __name__ == "__main__":
    unittest.main()
