import unittest

from apps.api.safety import ApprovalService


class ApprovalsUnitTest(unittest.TestCase):
    def test_create_and_decide_approval(self) -> None:
        approvals = ApprovalService()
        request = approvals.create_request(
            workspace_id="ws-approval",
            actor_id="member-1",
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
                actor_id="member-1",
                capability="external_action",
                action="delegate:spec:goal",
            )
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
