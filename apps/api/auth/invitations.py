import secrets
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Literal

from apps.api.db.state import connect_state_db

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
    def __init__(
        self,
        *,
        database_path: str | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> None:
        self._connection = connection
        self._owns_connection = False
        if self._connection is None and database_path is not None:
            self._connection = connect_state_db(database_path)
            self._owns_connection = True

        self._invitations: dict[str, Invitation] = {}
        self._memberships_by_workspace: dict[str, list[WorkspaceMembership]] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    def _invitations_from_db(
        self,
        *,
        workspace_id: str,
    ) -> list[Invitation]:
        if self._connection is None:
            raise RuntimeError("database connection is required")

        cursor = self._connection.execute(
            """
            select token, workspace_id, email, role, invited_by, created_at, expires_at, accepted
            from invitation_record
            where workspace_id = ?
            order by created_at asc
            """,
            (workspace_id,),
        )
        rows = cursor.fetchall()
        return [
            Invitation(
                token=row[0],
                workspace_id=row[1],
                email=row[2],
                role=row[3],
                invited_by=row[4],
                created_at=row[5],
                expires_at=row[6],
                accepted=bool(row[7]),
            )
            for row in rows
        ]

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
        if self._connection is None:
            self._invitations[invitation.token] = invitation
        else:
            self._connection.execute(
                """
                insert into invitation_record (
                  token, workspace_id, email, role, invited_by, created_at, expires_at, accepted
                ) values (?, ?, ?, ?, ?, ?, ?, 0)
                """,
                (
                    invitation.token,
                    invitation.workspace_id,
                    invitation.email,
                    invitation.role,
                    invitation.invited_by,
                    invitation.created_at,
                    invitation.expires_at,
                ),
            )
            self._connection.commit()
        return invitation

    def list_invitations(
        self,
        *,
        workspace_id: str,
        include_accepted: bool = True,
    ) -> list[Invitation]:
        if self._connection is not None:
            invitations = self._invitations_from_db(workspace_id=workspace_id)
            if include_accepted:
                return invitations
            return [invitation for invitation in invitations if not invitation.accepted]

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
        invitation: Invitation | None
        if self._connection is None:
            invitation = self._invitations.get(token)
        else:
            cursor = self._connection.execute(
                """
                select token, workspace_id, email, role,
                       invited_by, created_at, expires_at, accepted
                from invitation_record
                where token = ?
                """,
                (token,),
            )
            row = cursor.fetchone()
            invitation = (
                None
                if row is None
                else Invitation(
                    token=row[0],
                    workspace_id=row[1],
                    email=row[2],
                    role=row[3],
                    invited_by=row[4],
                    created_at=row[5],
                    expires_at=row[6],
                    accepted=bool(row[7]),
                )
            )
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
        if self._connection is None:
            self._invitations[token] = accepted
        else:
            self._connection.execute(
                "update invitation_record set accepted = 1 where token = ?",
                (token,),
            )

        membership = WorkspaceMembership(
            workspace_id=invitation.workspace_id,
            user_id=user_id,
            role=invitation.role,
            invited_via=token,
        )
        if self._connection is None:
            members = self._memberships_by_workspace.setdefault(invitation.workspace_id, [])
            members.append(membership)
        else:
            self._connection.execute(
                """
                insert or replace into workspace_membership_record (
                  workspace_id, user_id, role, invited_via, created_at
                ) values (?, ?, ?, ?, ?)
                """,
                (
                    membership.workspace_id,
                    membership.user_id,
                    membership.role,
                    membership.invited_via,
                    datetime.now(timezone.utc).isoformat(),
                ),
            )
            self._connection.commit()
        return membership

    def list_memberships(self, *, workspace_id: str | None = None) -> list[WorkspaceMembership]:
        if self._connection is not None:
            if workspace_id is None:
                cursor = self._connection.execute(
                    """
                    select workspace_id, user_id, role, invited_via
                    from workspace_membership_record
                    order by created_at asc
                    """
                )
            else:
                cursor = self._connection.execute(
                    """
                    select workspace_id, user_id, role, invited_via
                    from workspace_membership_record
                    where workspace_id = ?
                    order by created_at asc
                    """,
                    (workspace_id,),
                )
            rows = cursor.fetchall()
            return [
                WorkspaceMembership(
                    workspace_id=row[0],
                    user_id=row[1],
                    role=row[2],
                    invited_via=row[3],
                )
                for row in rows
            ]

        if workspace_id is not None:
            return list(self._memberships_by_workspace.get(workspace_id, []))

        memberships: list[WorkspaceMembership] = []
        for workspace_memberships in self._memberships_by_workspace.values():
            memberships.extend(workspace_memberships)
        return memberships
