# QA Agent

QA Agent is a release quality control layer for teams that want to scale AI Coding without scaling release risk.

The repository starts with a strategy and contract-first implementation plan:

```text
Product Spec defines truth.
QA Agent drafts and analyzes.
Framework validates contracts and dry-run readiness.
Human Release Quality Owner approves business truth and release readiness.
AI Coding scales only after QA readiness is proven.
```

## Repository Layout

| Path | Purpose |
|---|---|
| `docs/strategy/` | Strategy proposals and decision framing. |
| `docs/architecture/` | Operating model, ownership, lifecycle, and control rules. |
| `docs/contracts/` | YAML contracts that should become framework/agent inputs and outputs. |
| `docs/roadmap/` | Implementation stages and acceptance gates. |

## Current Documents

- [QA Control Layer Strategy](docs/strategy/qa-control-layer-before-ai-coding.md)
- [Operating Model](docs/architecture/operating-model.md)
- [Stage 0 Implementation Plan](docs/roadmap/stage-0-implementation-plan.md)
- [Release Testing Input Contract](docs/contracts/release-testing-input.v0.1.yaml)
- [Dry-run Readiness Report Contract](docs/contracts/dry-run-readiness-report.v0.1.yaml)
- [Approval Record Contract](docs/contracts/approval-record.v0.1.yaml)

## Stage 0 Focus

Stage 0 is intentionally split into small gates:

```text
0A - Framework validation foundation
0B - Dry-run planner and readiness report
0C - QA Agent MVP and repair loop
```

The first hard gate is not code generation. It is whether generated release testing artifacts can be validated, dry-run, reviewed, and approved without bypassing human ownership of business truth.
