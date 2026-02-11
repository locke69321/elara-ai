from apps.api.agents.policy import ActorContext


class WorkspaceAccessService:
    """In-memory workspace access registry for owner/member authorization."""

    def __init__(self) -> None:
        self._owner_by_workspace: dict[str, str] = {}
        self._member_ids_by_workspace: dict[str, set[str]] = {}

    def ensure_workspace_access(self, *, workspace_id: str, actor: ActorContext) -> None:
        owner_id = self._owner_by_workspace.get(workspace_id)
        members = self._member_ids_by_workspace.get(workspace_id, set())

        if owner_id is None:
            if actor.role == "owner":
                self._owner_by_workspace[workspace_id] = actor.user_id
                return

            if actor.user_id in members:
                return

            raise PermissionError("actor is not authorized for this workspace")

        if actor.role == "owner":
            if actor.user_id != owner_id:
                raise PermissionError("actor is not authorized for this workspace")
            return

        if actor.user_id not in members:
            raise PermissionError("actor is not authorized for this workspace")

    def add_workspace_member(self, *, workspace_id: str, user_id: str) -> None:
        members = self._member_ids_by_workspace.setdefault(workspace_id, set())
        members.add(user_id)
