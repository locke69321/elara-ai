# Agent Studio Guide

## Purpose

Agent Studio controls specialist agents used by Execution mode delegation.

## Core Model

Each specialist has:
- `id`: stable identifier
- `name`: display name
- `prompt`: execution instructions
- `soul`: behavior/personality profile
- `capabilities`: permitted actions

Supported capabilities:
- `read_memory`
- `write_memory`
- `run_tool`
- `delegate`
- `external_action`

## Role Rules

- `owner`: can create and edit specialist definitions.
- `member`: can use specialists but cannot create/edit definitions.

Attempting owner-only operations as `member` returns `403`.

## Create a Specialist (API)

```bash
curl -X POST http://localhost:8000/workspaces/ws1/specialists \
  -H 'content-type: application/json' \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner' \
  -d '{
    "id":"spec-analysis",
    "name":"Analysis Specialist",
    "prompt":"Analyze and summarize",
    "soul":"Methodical",
    "capabilities":["delegate","write_memory"]
  }'
```

## High-Impact Capabilities and Approvals

Specialists with `run_tool` or `external_action` require explicit approval before execution.

Execution response returns `409` with `approval_id` when approval is required.

Approval flow:
1. Execute goal and capture `approval_id`.
2. Owner approves:

```bash
curl -X POST http://localhost:8000/approvals/<approval_id>/decision \
  -H 'content-type: application/json' \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner' \
  -d '{"decision":"approved"}'
```

3. Re-run goal with approved request ID:

```bash
curl -X POST http://localhost:8000/workspaces/ws1/execution/goals \
  -H 'content-type: application/json' \
  -H 'x-user-id: owner-1' \
  -H 'x-user-role: owner' \
  -d '{
    "goal":"perform approved action",
    "approved_request_ids":["<approval_id>"]
  }'
```

## Recommended Specialist Design

- Keep prompts narrow and task-oriented.
- Use capabilities minimally (principle of least privilege).
- Avoid high-impact capabilities unless the workflow explicitly needs them.
- Use descriptive `id` values for audit readability.
