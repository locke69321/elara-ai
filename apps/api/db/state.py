import os
import sqlite3


def resolve_state_db_path(database_path: str | None = None) -> str:
    if database_path is not None:
        return database_path
    return os.getenv("ELARA_STATE_DB_PATH", ":memory:")


def ensure_state_schema(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA foreign_keys = ON;")
    connection.executescript(
        """
        create table if not exists invitation_record (
          token text primary key,
          workspace_id text not null,
          email text not null,
          role text not null,
          invited_by text not null,
          created_at text not null,
          expires_at text not null,
          accepted integer not null check (accepted in (0, 1))
        );

        create table if not exists workspace_membership_record (
          workspace_id text not null,
          user_id text not null,
          role text not null,
          invited_via text not null,
          created_at text not null,
          primary key (workspace_id, user_id)
        );

        create table if not exists workspace_owner_record (
          workspace_id text primary key,
          owner_id text not null,
          created_at text not null
        );

        create table if not exists approval_request_record (
          id text primary key,
          workspace_id text not null,
          actor_id text not null,
          capability text not null,
          action text not null,
          reason text not null,
          status text not null,
          created_at text not null,
          decided_at text,
          decided_by text
        );

        create table if not exists audit_event_record (
          id text primary key,
          workspace_id text not null,
          actor_id text not null,
          action text not null,
          outcome text not null,
          metadata_json text not null,
          previous_hash text not null,
          event_hash text not null,
          created_at text not null
        );
        create index if not exists idx_audit_event_workspace_created
          on audit_event_record(workspace_id, created_at);

        create table if not exists run_event_record (
          agent_run_id text not null,
          seq integer not null,
          event_type text not null,
          payload_json text not null,
          created_at text not null,
          primary key (agent_run_id, seq)
        );

        create table if not exists run_event_outbox_record (
          agent_run_id text not null,
          seq integer not null,
          published integer not null default 0 check (published in (0, 1)),
          primary key (agent_run_id, seq),
          foreign key (agent_run_id, seq)
            references run_event_record(agent_run_id, seq)
            on delete cascade
        );

        create table if not exists run_access_record (
          agent_run_id text not null,
          workspace_id text not null,
          actor_id text not null,
          primary key (agent_run_id, actor_id)
        );

        create table if not exists memory_record (
          backend text not null,
          workspace_id text not null,
          agent_id text not null,
          memory_id text not null,
          content text not null,
          embedding_model text not null,
          embedding_dim integer not null,
          embedding_json text,
          created_at text not null,
          updated_at text not null,
          primary key (backend, workspace_id, agent_id, memory_id)
        );
        """
    )
    connection.commit()


def connect_state_db(database_path: str | None = None) -> sqlite3.Connection:
    path = resolve_state_db_path(database_path)
    connection = sqlite3.connect(path, check_same_thread=False)
    ensure_state_schema(connection)
    return connection
