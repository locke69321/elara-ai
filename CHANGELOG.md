# Changelog

All notable changes to this project will be documented in this file.

## [0.0.2](https://github.com/locke69321/elara-ai/compare/v0.0.1...v0.0.2) (2026-02-12)


### Features

* complete v0.1 gap closure and governance rollout ([#1](https://github.com/locke69321/elara-ai/issues/1)) ([45978dd](https://github.com/locke69321/elara-ai/commit/45978dd92181ed372e22ef76e36fac930b674ada))
* **phase2:** add dual-mode runtime, policy, and workflow routes ([670f5ae](https://github.com/locke69321/elara-ai/commit/670f5ae8727cad6d4b608c75e501295415409f82))
* **phase3:** add security hardening and operability workflows ([b745cdc](https://github.com/locke69321/elara-ai/commit/b745cdc42f0a638e819774e7421b09d46357fdd6))


### Bug Fixes

* **api:** block cross-owner approval decisions ([6e63db0](https://github.com/locke69321/elara-ai/commit/6e63db0e75d49dd4b2378ee359a22bbb38fa79f5))
* **api:** enforce tenant isolation and block member high-impact delegation ([a5c420d](https://github.com/locke69321/elara-ai/commit/a5c420dba921d6c8cc0ac0633105080b766b7e59))
* **api:** redact invitation tokens in audit metadata ([1097b52](https://github.com/locke69321/elara-ai/commit/1097b5292de8aa6021fa5ed3c3051e8742c6818c))
* **api:** require explicit actor headers ([547274f](https://github.com/locke69321/elara-ai/commit/547274f6f46ade90efbe2cbba0e36f9b9a149b17))
* **api:** secure agent run replay access and payloads ([b466502](https://github.com/locke69321/elara-ai/commit/b466502e2325ac2e4115f7ccf026245851c437ce))

## v0.0.1 - Initial Public Publish

Release notes: `docs/releases/v0.0.1-initial-publish.md`

### Included Commits

- `a4b837e` chore(core): bootstrap repository and local uv/pnpm workflow
- `670f5ae` feat(phase2): add dual-mode runtime, policy, and workflow routes
- `93d864e` chore(quality): enforce strict gates and codify outside-in tdd
- `b745cdc` feat(phase3): add security hardening and operability workflows
- `0d74ef9` docs(phase4): add setup, user guides, and backup restore runbook

### Highlights

- Monorepo scaffold for API, web, worker, contracts, and plan-driven delivery.
- Dual-mode runtime (companion + execution) with specialist orchestration.
- Security hardening with invitation, approvals, audit chain, and SQLCipher startup checks.
- Strict engineering gates with lint/type/no-any/coverage enforcement.
- Setup, user, security, and operations documentation for self-hosted usage.
