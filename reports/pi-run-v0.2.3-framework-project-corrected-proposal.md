# pi-run v0.2.3 Corrected Proposal Index Only

Date: 2026-07-05 Asia/Taipei

Status: Superseded by separate owner documents

This joint proposal file is intentionally index-only. Do not add framework-owned or project-owned proposal content here.

It was split to avoid mixing framework-owned fixes with project/pi-run-owned harness work.

Use these files instead:

- Framework-only proposal: `reports/pi-run-v0.2.3-framework-corrected-proposal.md`
- Project/pi-run-only proposal: `reports/pi-run-v0.2.3-project-corrected-proposal.md`

Boundary summary:

- Framework owns suite-mode runtime, validation, evidence validation, reporting, provider contracts, provider registry, CLI behavior, and release asset metadata.
- Project/pi-run owns release asset download/verification, dependency provisioning, artifact materialization, framework invocation, evidence collation, cleanup, and acceptance reporting.
- The framework must not expose public `pi-run`; direct public RP-mode is obsolete.
- Testcontainers/Docker provisioning belongs to project/pi-run, not the framework jar.
