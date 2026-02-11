---
date: 2026-02-10
topic: agent-native-companion-platform
---

# Agent-Native Companion Platform

## What We're Building
Build a self-hosted web app where users interact with one or two primary agents for both conversation and goal execution, while those primary agents can coordinate a customizable team of specialist agents. The product supports chat, roleplay, and task orchestration as equal first-class experiences, not separate products.

The v1 target is a privacy-conscious system for solo power users and small trusted groups. Agents are customizable with distinct system prompts, "souls" (identity/personality profiles), and persistent memory. Memory is database-first: SQLite by default (including vectors), with PostgreSQL + pgvector and Supabase supported out of the box. The product should remain modular so users install only needed capabilities, avoiding a kitchen-sink bundle.

## Why This Approach
We considered companion-first, orchestrator-first, and dual-mode options. Dual-mode was selected because the core user value is the combination of meaningful companionship and practical execution. A companion-first design risks weak execution features; an orchestrator-first design risks transactional UX that underdelivers on personality and roleplay.

Dual-mode keeps one identity, memory, and safety model across both interaction styles, which reduces long-term product fragmentation and rework. This also aligns with a modular architecture where features can be enabled or omitted per deployment.

## Key Decisions
- Dual-mode v1 (`Companion` + `Execution`) is first-class: The product promise depends on both emotional continuity and practical outcomes.
- Deployment target is self-hosted web: Fits control/privacy goals while supporting multi-device usage.
- User model is single-owner default with optional invited users: Covers solo and small trusted groups without full enterprise complexity.
- Database-first memory strategy: SQLite is default; PostgreSQL/pgvector and Supabase are first-class options.
- Security baseline is non-optional: Encryption at rest and reasonable safety controls are part of the foundation, not add-ons.
- Modular packaging over kitchen sink: Users should not download unused models/integrations/features by default.
- Explicit v2 deferral: Advanced multi-tenant org administration is out of v1 scope.

## Open Questions
- What is the minimum acceptable safety policy set for autonomous agent actions in v1?
- What exact permission model should separate primary agents, specialist agents, and human users?
- How much roleplay flexibility is acceptable before requiring stricter safety guardrails?
- What migration and portability guarantees should exist between SQLite and PostgreSQL/Supabase memory backends?

## Next Steps
→ `/prompts:workflows-plan` for implementation details
