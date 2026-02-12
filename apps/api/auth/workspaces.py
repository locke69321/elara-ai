import sqlite3
from datetime import datetime, timezone

from apps.api.agents.policy import ActorContext
from apps.api.db.state import connect_state_db


class WorkspaceAccessService:
    """Workspace access registry with optional durable owner persistence."""

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
        self._owner_by_workspace: dict[str, str] = {}
        self._member_ids_by_workspace: dict[str, set[str]] = {}

    def close(self) -> None:
        if self._connection is None or not self._owns_connection:
            return
        self._connection.close()
        self._connection = None

    def __del__(self) -> None:
        self.close()

    def _owner_from_db(self, *, workspace_id: str) -> str | None:
        if self._connection is None:
            return None
        cursor = self._connection.execute(
            """
            select owner_id
            from workspace_owner_record
            where workspace_id = ?
            """,
            (workspace_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return str(row[0])

    def _hydrate_owner_from_db(self, *, workspace_id: str) -> str | None:
        owner_id = self._owner_by_workspace.get(workspace_id)
        if owner_id is not None:
            return owner_id
        owner_id = self._owner_from_db(workspace_id=workspace_id)
        if owner_id is not None:
            self._owner_by_workspace[workspace_id] = owner_id
        return owner_id

    def list_workspace_owners(self) -> list[tuple[str, str]]:
        if self._connection is None:
            return sorted(self._owner_by_workspace.items(), key=lambda item: item[0])
        cursor = self._connection.execute(
            """
            select workspace_id, owner_id
            from workspace_owner_record
            order by created_at asc
            """
        )
        rows = cursor.fetchall()
        return [(str(row[0]), str(row[1])) for row in rows]

    def add_workspace_owner(self, *, workspace_id: str, owner_id: str) -> None:
        self._owner_by_workspace[workspace_id] = owner_id

    def ensure_workspace_access(self, *, workspace_id: str, actor: ActorContext) -> None:
        owner_id = self._hydrate_owner_from_db(workspace_id=workspace_id)
        members = self._member_ids_by_workspace.get(workspace_id, set())

        if owner_id is None:
            if actor.role == "owner":
                self._owner_by_workspace[workspace_id] = actor.user_id
                if self._connection is not None:
                    try:
                        self._connection.execute(
                            """
                            insert into workspace_owner_record (
                              workspace_id, owner_id, created_at
                            ) values (?, ?, ?)
                            """,
                            (
                                workspace_id,
                                actor.user_id,
                                datetime.now(timezone.utc).isoformat(),
                            ),
                        )
                        self._connection.commit()
                    except sqlite3.IntegrityError as error:
                        existing_owner_id = self._owner_from_db(workspace_id=workspace_id)
                        if existing_owner_id is None:
                            raise
                        self._owner_by_workspace[workspace_id] = existing_owner_id
                        if existing_owner_id != actor.user_id:
                            raise PermissionError(
                                "actor is not authorized for this workspace"
                            ) from error
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
