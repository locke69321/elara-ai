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

    def test_member_cannot_delegate_high_impact_capabilities(self) -> None:
        engine = PolicyEngine()
        actor = ActorContext(user_id="u1", role="member")

        decision = engine.can_delegate(
            actor=actor,
            capabilities={"delegate", "external_action"},
        )

        self.assertFalse(decision.allowed)
        self.assertIn("high-impact", decision.reason or "")

    def test_allowed_tools_are_permitted(self) -> None:
        engine = PolicyEngine()
        decision = engine.can_use_tool(tool_name="search_docs")
        self.assertTrue(decision.allowed)

    def test_non_allowlisted_tool_is_rejected(self) -> None:
        engine = PolicyEngine()
        decision = engine.can_use_tool(tool_name="shell_exec")
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "tool is not in allowlist")


if __name__ == "__main__":
    unittest.main()
