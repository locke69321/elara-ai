import unittest
from dataclasses import replace

from apps.api.audit import ImmutableAuditLog


class AuditLogUnitTest(unittest.TestCase):
    def test_append_and_verify_chain(self) -> None:
        audit_log = ImmutableAuditLog()
        audit_log.append_event(
            workspace_id="ws-audit",
            actor_id="owner-1",
            action="test.action",
            outcome="success",
            metadata={"k": "v"},
        )
        audit_log.append_event(
            workspace_id="ws-audit",
            actor_id="owner-1",
            action="test.action.2",
            outcome="success",
            metadata={},
        )

        self.assertTrue(audit_log.verify_chain(workspace_id="ws-audit"))

    def test_verify_chain_detects_tampering(self) -> None:
        audit_log = ImmutableAuditLog()
        event = audit_log.append_event(
            workspace_id="ws-audit",
            actor_id="owner-1",
            action="test.action",
            outcome="success",
            metadata={"k": "v"},
        )

        tampered = replace(event, outcome="tampered")
        audit_log._events_by_workspace["ws-audit"] = [tampered]

        self.assertFalse(audit_log.verify_chain(workspace_id="ws-audit"))


if __name__ == "__main__":
    unittest.main()
