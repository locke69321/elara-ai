import os
import tempfile
import unittest

from apps.api.safety import ApprovalService


class ApprovalsUnitTest(unittest.TestCase):
    def test_approvals_persist_across_service_instances_when_db_path_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "approvals.sqlite3")
            first = ApprovalService(database_path=db_path)
            request = first.create_request(
                workspace_id="ws-approval-persist",
                actor_id="owner-1",
                capability="run_tool",
                action="delegate:spec:goal",
                reason="persist me",
            )

            second = ApprovalService(database_path=db_path)
            persisted = second.get_request(approval_id=request.id)
            self.assertIsNotNone(persisted)
            if persisted is not None:
                self.assertEqual(persisted.workspace_id, "ws-approval-persist")

    def test_create_and_decide_approval(self) -> None:
        approvals = ApprovalService()
        request = approvals.create_request(
            workspace_id="ws-approval",
            actor_id="owner-1",
            capability="external_action",
            action="delegate:spec:goal",
            reason="need confirmation",
        )

        decided = approvals.decide_request(
            approval_id=request.id,
            approver_id="owner-1",
            decision="approved",
        )

        self.assertEqual(decided.status, "approved")
        self.assertTrue(
            approvals.is_approved(
                approval_id=request.id,
                workspace_id="ws-approval",
                actor_id="owner-1",
                capability="external_action",
                action="delegate:spec:goal",
            )
        )

    def test_deciding_request_with_different_approver_fails(self) -> None:
        approvals = ApprovalService()
        request = approvals.create_request(
            workspace_id="ws-approval",
            actor_id="owner-a",
            capability="run_tool",
            action="delegate:spec:goal",
            reason="need confirmation",
        )

        with self.assertRaises(PermissionError):
            approvals.decide_request(
                approval_id=request.id,
                approver_id="owner-b",
                decision="approved",
            )

    def test_deciding_missing_request_fails(self) -> None:
        approvals = ApprovalService()

        with self.assertRaises(ValueError):
            approvals.decide_request(
                approval_id="missing",
                approver_id="owner-1",
                decision="approved",
            )


if __name__ == "__main__":
    unittest.main()
