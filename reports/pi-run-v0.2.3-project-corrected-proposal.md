# pi-run v0.2.3 Project Corrected Proposal

Date: 2026-07-05 Asia/Taipei

Status: Proposed after review

Owner: Project-side pi-run harness in `/Users/herman_mbp2023/Documents/test_framework_pirun`

Scope: Project/pi-run-owned release acceptance, provisioning, matrix generation, execution, reporting, and cleanup. This proposal does not require the framework jar to provision Docker/Testcontainers dependencies.

Separation rule: this file tracks only project-side pi-run harness work in this repository. Framework release changes belong in `reports/pi-run-v0.2.3-framework-corrected-proposal.md`.

## Evidence Baseline

Based on v0.2.3 release assets only:

- `release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar`
- `usage-kit-v0.2.3/usage-kit`
- `release-assets-v0.2.3/checksums.sha256`
- `reports/pi-run-v0.2.3-report.md`

Current project-side evidence:

- `.pirun/runs/PIRUN-V023-NATS-2/nats_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-WIREMOCK-3/wiremock_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-JDBC-2/jdbc_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-FULL-4/contract_baseline/project_report.json`

Observed result:

| Mode | Status | Note |
|---|---:|---|
| `nats-only` | PASS | Project Docker NATS was consumed by framework runtime. |
| `wiremock-only` | PASS with caveat | Project Docker WireMock started, but external `base_url` consumption is NOT_PROVEN. |
| `jdbc-lightweight` | PASS | Lightweight/embedded JDBC path executed. |
| `full-contract-baseline` | PASS with caveat | Mixed suite passed; WireMock external URL remains NOT_PROVEN. |
| Docker cleanup | PASS | Final run IDs had zero leftover containers. |

## Project Boundary

The project-side pi-run harness owns:

- release asset download and checksum/signature verification;
- dependency provisioning and readiness checks;
- suite artifact materialization;
- framework jar invocation;
- provisioning-vs-consumption evidence;
- full function coverage matrix generation;
- report collation and cleanup.

The project-side harness must not:

- ask the framework jar to provision Testcontainers;
- rely on GitHub source archives as acceptance inputs;
- claim native/ephemeral support for framework contract-only modes;
- hide blocked rows from the final report;
- treat provisioning success as framework consumption proof.

## PRJ-P0-001: Generate a Full Function Coverage Matrix

Problem:

The project-side matrix must not be hand-maintained. It should be generated from the release usage-kit so coverage gaps are reproducible.

Required change:

- Add `pirun/inspect_usage_kit.py`.
- Read the selected release usage-kit paths:
  - `docs/02-architecture/contracts/provider_capability_registry.v0.2.yaml`
  - `docs/02-architecture/contracts/provider-contracts/*.yaml`
  - `docs/09-operations/provider_support_matrix.md`
  - `samples/**/suite_manifest.yaml`
  - `samples/**/test_case*.yaml`
  - `release/verification_commands.md`
- Emit:
  - `reports/pi-run-v0.2.3-function-coverage-matrix.json`
  - `reports/pi-run-v0.2.3-function-coverage-matrix.md`

Each matrix row should include:

```yaml
provider_type:
runtime_status:
runtime_modes:
contract_exists:
direct_sample:
indirect_sample:
sample_paths:
release_verification_command:
runnable_now:
expected_status:
owner:
resource_class:
reason:
```

Expected status values:

- `PASS`
- `EXPECTED_FAIL`
- `BLOCKED_CONTRACT_MISSING`
- `BLOCKED_DEPRECATED_ALIAS`
- `BLOCKED_FRAMEWORK_CONTRACT_ONLY`
- `BLOCKED_RESOURCE`
- `BLOCKED_LICENSE`
- `BLOCKED_USAGE_KIT_SAMPLE_GAP`

`NOT_PROVEN` is reserved for provisioning-vs-consumption evidence where a project dependency was started but the framework did not prove it consumed that dependency, such as project-provisioned WireMock external `base_url`.

Acceptance:

```text
generated_matrix_rows > 0
manual_matrix_rows = 0
all_non_runnable_rows_have_reason = true
all_provider_registry_rows_accounted_for = true
```

## PRJ-P0-002: Add a Generic Usage-kit Matrix Runner

Required change:

- Add `pirun/run_usage_kit_matrix.py`.
- Consume the generated matrix and release asset paths.
- Execute only rows marked runnable by the generated release usage-kit matrix.
- Record skipped/blocked rows with reason instead of silently omitting them.
- Run low-memory Java commands:

```bash
java -Xmx512m -jar release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar validate --suite <suite> --profile <profile>
java -Xmx512m -jar release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar run --suite <suite> --profile <profile> --dry-run
java -Xmx512m -jar release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar run --suite <suite> --profile <profile>
java -Xmx512m -jar release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar validate-evidence --result <result.json>
java -Xmx512m -jar release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar report --result <result.json> --format text
```

Acceptance:

```text
all_runnable_rows_have_command_evidence = true
all_blocked_rows_have_expected_status_and_reason = true
unexpected_failures = 0
```

## PRJ-P0-003: Record Provisioning and Consumption Separately

Problem:

Provisioning success does not prove framework consumption. WireMock v0.2.3 showed this exactly.

Required change:

- Keep these fields in every project report:
  - `project_provisioned`
  - `project_readiness_passed`
  - `framework_runtime_executed`
  - `framework_consumed_project_dependency`
  - `framework_consumption_status`
  - `consumed_binding_keys`
  - `not_proven_reason`
- Treat project-provisioned WireMock external `base_url` as `NOT_PROVEN` until the framework proves consumption.
- Treat framework-managed WireMock as a separate passing capability.

Acceptance:

```yaml
wiremock_framework_managed:
  status: PASS
wiremock_project_external_base_url:
  status: NOT_PROVEN
  reason: external_base_url_not_consumed_by_framework_provider_capability
```

## PRJ-P0-004: Resource and Support Gating

Required change:

- Keep default local pi-run under the 8G machine limit.
- Continue using:
  - NATS Docker with a small memory cap;
  - WireMock Docker with a small memory cap;
  - lightweight JDBC/H2 path.
- Do not start Oracle XE, DB2, Kafka, or IBM MQ by default.
- Do not promise Kafka/IBM MQ native or ephemeral Testcontainers runs while the framework marks those modes as contract-only.
- Command-capable providers are not blocked by project-side safety policy. If the release usage-kit has no executable sample for a command-capable provider/runtime row, keep it as `BLOCKED_USAGE_KIT_SAMPLE_GAP`.

Default local policy:

| Dependency | Default action | Reason |
|---|---|---|
| NATS | run lightweight container | Already proven and low footprint. |
| WireMock | run lightweight container for project provisioning proof | Consumption remains NOT_PROVEN until framework supports external URL. |
| JDBC | use embedded/lightweight path | Avoid heavy DB containers locally. |
| Oracle XE / DB2 | blocked by default | Too heavy for 8G local acceptance. |
| Kafka / IBM MQ | blocked as framework contract-only for native/ephemeral | Framework runtime does not yet support those modes. |
| K8s / VM / shell / external runner | blocked when release sample is absent | Do not invent project-side safety-policy blockers; use release sample coverage truthfully. |

## PRJ-P0-005: Release Asset Verification

Required change:

- Verify checksums for jar and usage-kit zip.
- Verify detached signatures if the release publishes them.
- If signatures are not available, record `signature_verification: not_available` and keep the final decision explicit.
- Do not use GitHub source archives as framework acceptance inputs.

Acceptance:

```yaml
release_source: github_release_assets
source_archive_used: false
checksum_verification: passed
signature_verification: passed_or_not_available
```

## PRJ-P0-006: Cleanup and Evidence Inventory

Required change:

- Ensure all project-started Docker containers are removed even when framework execution fails.
- Write partial reports on provisioning or framework failures.
- Add zero-leftover verification per run ID.
- Scan project reports for accidental raw secrets before publishing reports.

Acceptance:

```text
leftover_containers_for_run_id = 0
partial_report_written_on_failure = true
raw_secret_scan = passed
```

## Corrected Orchestration Order

```text
nats-only
  -> wiremock-only
  -> jdbc-lightweight
  -> full-contract-baseline
  -> generated usage-kit coverage matrix
  -> runnable suite-mode matrix rows
  -> report/validate-evidence matrix rows
```

Blocked rows are part of the final report, not hidden failures.

## Project Deliverables

- `pirun/inspect_usage_kit.py`
- `pirun/run_usage_kit_matrix.py`
- `reports/pi-run-v0.2.3-function-coverage-matrix.json`
- `reports/pi-run-v0.2.3-function-coverage-matrix.md`
- `reports/pi-run-v0.2.3-full-coverage-report.md`
- `.pirun/runs/<run_id>/**/project_report.json`

## Project Acceptance Gate

```text
release asset checksum verification: PASS
release asset signature verification: PASS or explicitly NOT_AVAILABLE
source archive used: false
generated function coverage matrix: PASS
runnable suite-mode matrix rows: PASS
non-runnable rows: BLOCKED with correct reason
report positive cases: PASS
report negative cases: EXPECTED_FAIL
validate-evidence positive cases: PASS
validate-evidence negative cases: EXPECTED_FAIL
project-provisioned NATS consumption: PASS
project-provisioned WireMock external base_url consumption: PASS or NOT_PROVEN with framework issue
lightweight JDBC execution: PASS
Kafka/IBM MQ native/ephemeral: BLOCKED_FRAMEWORK_CONTRACT_ONLY unless future release changes support
command-capable providers without release samples: BLOCKED_USAGE_KIT_SAMPLE_GAP
Docker cleanup: PASS
raw secret scan: PASS
```

Until the framework implements or explicitly blocks project-provisioned WireMock external `base_url`, that row remains `NOT_PROVEN`, even when framework-managed WireMock capability samples pass.
