# AGENTS.md

Engineering operating guide for this repository.

## Core Rules

- Follow outside-in TDD for all feature and bug work.
- Use strict Red -> Green -> Refactor loops.
- Keep architecture boundaries explicit and test them.
- Prefer simple, incremental changes over large rewrites.

## Outside-In TDD Workflow

1. E2E (`apps/api/tests/e2e/`):
   - Start by writing/adjusting a failing test for user-visible behavior.
   - Validate request/response shape, auth/policy behavior, and primary flow.
2. Integration (`apps/api/tests/integration/`):
   - Add failing tests for component collaboration (runtime + policy + memory + events).
   - Verify contracts and ordering semantics.
3. Unit (`apps/api/tests/unit/`):
   - Add failing tests for isolated business logic.
   - Mock external dependencies and verify interactions.
4. Implement minimum code to pass.
5. Refactor while keeping tests green.

## Red Green Refactor Discipline

- Red: write the smallest failing test that expresses required behavior.
- Green: implement the minimum change to pass.
- Refactor: improve structure, names, and duplication with zero behavior change.
- Repeat in small cycles; do not batch many behavior changes into one loop.

## Mocking Policy

- Mock external dependencies only (LLM providers, network services, DB drivers, clocks/UUIDs when needed).
- Do not mock core domain logic under test.
- In unit tests, assert key dependency interactions (arguments and call count).
- In integration tests, prefer real in-memory adapters over mocks.

## Quality Gates (Must Pass)

- Lint: `make lint`
- Type safety: `make typecheck`
- Coverage: `make coverage`
- Full gate: `make check`

Coverage policy:

- Backend coverage must stay at or above 90% (`fail_under = 90`).
- New behavior must include tests at the appropriate layer(s).

## Type Safety Rules

- No explicit `Any` in authored production code.
- Keep Python types strict and complete.
- Keep TypeScript strict (`noImplicitAny` and strict mode).
- Prefer typed protocols/interfaces at boundaries.

## Definition of Done

- Behavior implemented via outside-in TDD loops.
- Relevant e2e/integration/unit tests added or updated.
- Lint, typecheck, and coverage gates all pass.
- Documentation and contracts updated when interfaces change.
