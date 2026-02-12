import os
import tempfile
import unittest
from dataclasses import replace

from apps.api.audit import ImmutableAuditLog


class AuditLogUnitTest(unittest.TestCase):
    def test_audit_events_persist_across_log_instances_when_db_path_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "audit.sqlite3")
            first_log = ImmutableAuditLog(database_path=db_path)
            first_log.append_event(
                workspace_id="ws-audit-persist",
                actor_id="owner-1",
                action="audit.persisted",
                outcome="success",
                metadata={"scope": "unit"},
            )

            second_log = ImmutableAuditLog(database_path=db_path)
            events = second_log.list_events(workspace_id="ws-audit-persist")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].action, "audit.persisted")

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
