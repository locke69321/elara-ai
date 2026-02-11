import os
import tempfile
import unittest

from apps.api.auth import InvitationService


class InvitationsUnitTest(unittest.TestCase):
    def test_invitations_persist_across_service_instances_when_db_path_is_used(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "invitations.sqlite3")
            first = InvitationService(database_path=db_path)
            invite = first.create_invitation(
                workspace_id="ws-invite-persist",
                email="persist@example.com",
                invited_by="owner-1",
            )

            second = InvitationService(database_path=db_path)
            invitations = second.list_invitations(workspace_id="ws-invite-persist")
            self.assertEqual([item.token for item in invitations], [invite.token])

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

    def test_list_memberships_without_workspace_returns_all_memberships(self) -> None:
        invitations = InvitationService()
        first = invitations.create_invitation(
            workspace_id="ws-a",
            email="a@example.com",
            invited_by="owner-1",
        )
        second = invitations.create_invitation(
            workspace_id="ws-b",
            email="b@example.com",
            invited_by="owner-1",
        )
        invitations.accept_invitation(token=first.token, user_id="member-a")
        invitations.accept_invitation(token=second.token, user_id="member-b")

        memberships = invitations.list_memberships()
        self.assertEqual(
            {(membership.workspace_id, membership.user_id) for membership in memberships},
            {("ws-a", "member-a"), ("ws-b", "member-b")},
        )


if __name__ == "__main__":
    unittest.main()
