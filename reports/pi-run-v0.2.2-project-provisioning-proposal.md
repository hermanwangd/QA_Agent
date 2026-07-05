# PI-run Project Provisioning Proposal for v0.2.2 Findings

Date: 2026-07-04 Asia/Taipei

Target owner: PI-run project under `/Users/herman_mbp2023/Documents/test_framework_pirun`

Scope: project-side Docker/Testcontainers provisioning and materialized run workspace creation. This proposal assumes the framework jar only consumes normal framework artifacts.

## Goal

Use project-side provisioning to start dependencies, fill standard framework artifact files, run the framework jar unchanged, and collect project provisioning evidence.

The project must not require framework-side `--binding-overrides` or framework-side generated-ref resolution.

## Target Flow

Use one orchestrator so cleanup runs even when framework execution, evidence validation, or reporting fails.

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode nats-only
```

The orchestrator must execute:

```text
start dependencies
materialize standard framework artifacts
invoke framework jar
validate evidence when result_json exists
run report when result_json exists
cleanup in finally
write project provisioning report
```

## Project Responsibilities

### PRJ-P0-001: Start dependencies

Start only what is needed for the selected suite/profile.

Initial POC order:

1. NATS only.
2. DB container.
3. WireMock mappings.
4. Full `contract_baseline`.

Docker is available at:

```text
/usr/local/bin/docker
```

Use full path or prepend `/usr/local/bin` to `PATH` in scripts.

Initial implementation mechanism:

- Use Python standard library subprocess calls to `/usr/local/bin/docker`.
- Do not introduce the Python `testcontainers` package until raw Docker lifecycle, labels, cleanup, and materialization are proven.
- Pin image tags and set resource limits.

Initial NATS image:

```text
nats:2.10-alpine
```

### PRJ-P0-002: Materialize standard framework artifacts

Project creates:

```text
.pirun/runs/<run_id>/contract_baseline/
  suite_manifest.yaml
  test_case.yaml
  env_profiles/ci.yaml
  environment_bindings/ci.yaml
  execution_profiles/ci_pr.yaml
  provider_instances/
  provider_contracts/
  fixtures/
  expected_results/
  logs/
    nats-startup.log
  provisioning_evidence.yaml
```

Rules:

- Copy source usage-kit files into run workspace.
- Replace all `generated://...` placeholders before framework execution.
- Do not write raw secret values to reportable YAML.
- Use `env://...` secret refs first because v0.2.2 examples prove `env://` is accepted as a secret reference scheme.
- Export the corresponding environment variables only for the framework process.

Example:

```yaml
environment_id: ci-contract-sample-materialized
profile: ci
provider_bindings:
  - provider_id: oracle-database
    runtime_mode: ephemeral
    binding_values:
      connection:
        secret_ref: env://PIRUN_ORACLE_CONNECTION
      dialect: oracle
  - provider_id: nats-event-bus
    runtime_mode: ephemeral
    binding_values:
      connection:
        secret_ref: env://PIRUN_NATS_CONNECTION
      subject: payments.accepted
      timeout: PT30S
      poll_interval: PT0.5S
```

### PRJ-P0-003: Write provisioning evidence

Create:

```yaml
provisioning_evidence_version: v0.1
run_id: <run_id>
profile: ci
dependencies:
  - provider_id: nats-event-bus
    provisioner: testcontainers
    image: nats:<tag>
    container_id: <container_id>
    mapped_ports:
      4222: <host_port>
    readiness:
      status: passed
      check: broker_connect
    logs_ref: logs/nats-startup.log
    cleanup:
      status: pending
evidence_classification: local_ci_ephemeral_only
downstream_release_evidence: false
```

Until framework evidence indexing of provisioning evidence is verified, this file is project-owned evidence. Do not assume framework `report --format yaml` includes it.

### PRJ-P0-004: Cleanup reliably

Stop and remove containers by run label:

```text
pirun.run_id=<run_id>
pirun.suite=contract_baseline
```

Acceptance:

```sh
/usr/local/bin/docker ps --filter label=pirun.run_id=<run_id>
```

returns no containers after cleanup.

The orchestrator must perform cleanup in `finally`, regardless of framework exit code.

## Security Rules

- Never write raw connection strings into reportable YAML.
- Prefer process-local `env://...` secret refs for the first POC.
- If secret files are introduced later, `.pirun/runs/**/secrets/*` and `.pirun/secrets/*` must be ignored by git, with `.gitkeep` allowed.
- Secret files, if introduced later, must use `0600` permissions.
- Evidence may include masked connection metadata only.
- Cleanup logs must not leak credentials.

## Acceptance Criteria

### POC NATS

```yaml
provider_runtime_invoked: true
provider_type: nats
evidence_classification: local_ci_ephemeral_only
release_evidence_eligible: false
cleanup_status: passed
```

During the v0.2.2 framework blocker window, the project-side POC may use:

```yaml
framework_result:
  run_status: blocked
  failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
project_provisioning_status: passed
materialization_status: passed
cleanup_status: passed
```

That is acceptable for project-side provisioning/materialization proof only, not full framework acceptance.

### Full Contract Baseline

```yaml
run_status: passed
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_types_used:
  - jdbc
  - nats
  - wiremock_http_mock
```

### Evidence And Report

```yaml
evidence_validation_status: passed
report_status: review_ready
missing_evidence_count: 0
masking_status: passed
release_evidence_eligible: false
```

## Current Blocker

Project-side materialization can be built independently, but full acceptance still requires the framework fix for:

```yaml
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
```

Until then, the project can prove provisioning and materialization, but the framework will still block `contract_baseline` before provider runtime.
