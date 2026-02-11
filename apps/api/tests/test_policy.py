import unittest
from typing import cast

from apps.api.agents.policy import ActorContext, PolicyEngine, Role


class PolicyEngineTest(unittest.TestCase):
    def test_member_cannot_edit_specialists(self) -> None:
        engine = PolicyEngine()
        actor = ActorContext(user_id="u1", role="member")

        decision = engine.can_edit_specialists(actor)

        self.assertFalse(decision.allowed)
        self.assertIn("owners", decision.reason or "")

    def test_owner_can_edit_specialists(self) -> None:
        engine = PolicyEngine()
        actor = ActorContext(user_id="u1", role="owner")

        decision = engine.can_edit_specialists(actor)

        self.assertTrue(decision.allowed)

    def test_delegate_requires_delegate_capability(self) -> None:
        engine = PolicyEngine()
        actor = ActorContext(user_id="u1", role="owner")

        decision = engine.can_delegate(actor=actor, capabilities={"write_memory"})

        self.assertFalse(decision.allowed)

    def test_delegate_rejects_unsupported_role(self) -> None:
        engine = PolicyEngine()
        actor = ActorContext(user_id="u1", role=cast(Role, "auditor"))

        decision = engine.can_delegate(actor=actor, capabilities={"delegate"})

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "unsupported actor role")


if __name__ == "__main__":
    unittest.main()
