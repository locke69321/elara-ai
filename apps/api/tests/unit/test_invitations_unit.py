import unittest

from apps.api.auth import InvitationService


class InvitationsUnitTest(unittest.TestCase):
    def test_owner_can_create_and_accept_invitation(self) -> None:
        invitations = InvitationService()
        invite = invitations.create_invitation(
            workspace_id="ws-invite",
            email="user@example.com",
            invited_by="owner-1",
        )

        membership = invitations.accept_invitation(token=invite.token, user_id="member-1")

        self.assertEqual(membership.workspace_id, "ws-invite")
        self.assertEqual(membership.user_id, "member-1")

    def test_cannot_accept_same_invitation_twice(self) -> None:
        invitations = InvitationService()
        invite = invitations.create_invitation(
            workspace_id="ws-invite",
            email="user@example.com",
            invited_by="owner-1",
        )
        invitations.accept_invitation(token=invite.token, user_id="member-1")

        with self.assertRaises(ValueError):
            invitations.accept_invitation(token=invite.token, user_id="member-2")


if __name__ == "__main__":
    unittest.main()
