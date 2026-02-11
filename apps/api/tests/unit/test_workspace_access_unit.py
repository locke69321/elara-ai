import os
import tempfile
import unittest

from apps.api.agents.policy import ActorContext
from apps.api.auth.workspaces import WorkspaceAccessService


class WorkspaceAccessUnitTest(unittest.TestCase):
    def test_first_owner_claims_workspace_access(self) -> None:
        access = WorkspaceAccessService()
        owner = ActorContext(user_id="owner-a", role="owner")

        access.ensure_workspace_access(workspace_id="ws-tenant", actor=owner)

    def test_cross_owner_is_denied_after_workspace_claim(self) -> None:
        access = WorkspaceAccessService()
        owner_a = ActorContext(user_id="owner-a", role="owner")
        owner_b = ActorContext(user_id="owner-b", role="owner")
        access.ensure_workspace_access(workspace_id="ws-tenant", actor=owner_a)

        with self.assertRaises(PermissionError):
            access.ensure_workspace_access(workspace_id="ws-tenant", actor=owner_b)

    def test_member_requires_membership_for_workspace_access(self) -> None:
        access = WorkspaceAccessService()
        owner = ActorContext(user_id="owner-a", role="owner")
        member = ActorContext(user_id="member-a", role="member")
        access.ensure_workspace_access(workspace_id="ws-tenant", actor=owner)

        with self.assertRaises(PermissionError):
            access.ensure_workspace_access(workspace_id="ws-tenant", actor=member)

        access.add_workspace_member(workspace_id="ws-tenant", user_id="member-a")
        access.ensure_workspace_access(workspace_id="ws-tenant", actor=member)

    def test_owner_persists_across_service_restart_with_state_db(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "workspace-access.sqlite3")
            owner_a = ActorContext(user_id="owner-a", role="owner")
            owner_b = ActorContext(user_id="owner-b", role="owner")

            first = WorkspaceAccessService(database_path=db_path)
            first.ensure_workspace_access(workspace_id="ws-tenant", actor=owner_a)
            first.close()

            second = WorkspaceAccessService(database_path=db_path)
            second.ensure_workspace_access(workspace_id="ws-tenant", actor=owner_a)
            with self.assertRaises(PermissionError):
                second.ensure_workspace_access(workspace_id="ws-tenant", actor=owner_b)
            second.close()


if __name__ == "__main__":
    unittest.main()
