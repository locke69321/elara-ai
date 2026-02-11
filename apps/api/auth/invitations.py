import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

InviteRole = Literal["member"]


@dataclass(frozen=True)
class Invitation:
    token: str
    workspace_id: str
    email: str
    role: InviteRole
    invited_by: str
    created_at: str
    expires_at: str
    accepted: bool


@dataclass(frozen=True)
class WorkspaceMembership:
    workspace_id: str
    user_id: str
    role: InviteRole
    invited_via: str


class InvitationService:
    def __init__(self) -> None:
        self._invitations: dict[str, Invitation] = {}
        self._memberships_by_workspace: dict[str, list[WorkspaceMembership]] = {}

    def create_invitation(
        self,
        *,
        workspace_id: str,
        email: str,
        invited_by: str,
        role: InviteRole = "member",
        ttl_hours: int = 72,
    ) -> Invitation:
        created_at = datetime.now(timezone.utc)
        invitation = Invitation(
            token=secrets.token_urlsafe(18),
            workspace_id=workspace_id,
            email=email,
            role=role,
            invited_by=invited_by,
            created_at=created_at.isoformat(),
            expires_at=(created_at + timedelta(hours=ttl_hours)).isoformat(),
            accepted=False,
        )
        self._invitations[invitation.token] = invitation
        return invitation

    def list_invitations(
        self,
        *,
        workspace_id: str,
        include_accepted: bool = True,
    ) -> list[Invitation]:
        invitations = [
            invitation
            for invitation in self._invitations.values()
            if invitation.workspace_id == workspace_id
        ]
        if include_accepted:
            return sorted(invitations, key=lambda invitation: invitation.created_at)

        pending = [invitation for invitation in invitations if not invitation.accepted]
        return sorted(pending, key=lambda invitation: invitation.created_at)

    def accept_invitation(self, *, token: str, user_id: str) -> WorkspaceMembership:
        invitation = self._invitations.get(token)
        if invitation is None:
            raise ValueError("invitation token not found")

        if invitation.accepted:
            raise ValueError("invitation has already been accepted")

        if datetime.fromisoformat(invitation.expires_at) <= datetime.now(timezone.utc):
            raise ValueError("invitation has expired")

        accepted = Invitation(
            token=invitation.token,
            workspace_id=invitation.workspace_id,
            email=invitation.email,
            role=invitation.role,
            invited_by=invitation.invited_by,
            created_at=invitation.created_at,
            expires_at=invitation.expires_at,
            accepted=True,
        )
        self._invitations[token] = accepted

        membership = WorkspaceMembership(
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role=invitation.role,
            invited_via=token,
        )
        members = self._memberships_by_workspace.setdefault(invitation.workspace_id, [])
        members.append(membership)
        return membership

    def list_memberships(self, *, workspace_id: str) -> list[WorkspaceMembership]:
        return list(self._memberships_by_workspace.get(workspace_id, []))
