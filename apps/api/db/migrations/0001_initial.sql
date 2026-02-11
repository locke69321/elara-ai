create table if not exists workspace (
  id integer primary key,
  name text not null,
  created_at text not null default current_timestamp
);

create table if not exists user_account (
  id integer primary key,
  email text not null unique,
  created_at text not null default current_timestamp
);

create table if not exists workspace_member (
  workspace_id integer not null,
  user_id integer not null,
  role text not null check (role in ('owner', 'member')),
  created_at text not null default current_timestamp,
  primary key (workspace_id, user_id),
  foreign key (workspace_id) references workspace(id) on delete cascade,
  foreign key (user_id) references user_account(id) on delete cascade
);

create table if not exists agent (
  id integer primary key,
  workspace_id integer not null,
  slug text not null,
  role text not null check (role in ('companion_primary', 'executor_primary', 'specialist')),
  created_at text not null default current_timestamp,
  unique (workspace_id, slug),
  foreign key (workspace_id) references workspace(id) on delete cascade
);

create table if not exists memory_item (
  id integer primary key,
  workspace_id integer not null,
  agent_id integer not null,
  memory_domain text not null check (memory_domain in ('episodic', 'semantic', 'working', 'soul')),
  payload text not null,
  created_at text not null default current_timestamp,
  foreign key (workspace_id) references workspace(id) on delete cascade,
  foreign key (agent_id) references agent(id) on delete cascade
);

create table if not exists agent_run (
  id integer primary key,
  workspace_id integer not null,
  agent_id integer not null,
  status text not null,
  created_at text not null default current_timestamp,
  foreign key (workspace_id) references workspace(id) on delete cascade,
  foreign key (agent_id) references agent(id) on delete cascade
);

create table if not exists agent_run_event (
  id integer primary key,
  agent_run_id integer not null,
  seq integer not null,
  event_type text not null,
  payload text not null,
  created_at text not null default current_timestamp,
  foreign key (agent_run_id) references agent_run(id) on delete cascade,
  unique (agent_run_id, seq)
);

create table if not exists agent_run_event_outbox (
  id integer primary key,
  agent_run_event_id integer not null unique,
  published_at text,
  created_at text not null default current_timestamp,
  foreign key (agent_run_event_id) references agent_run_event(id) on delete cascade
);
