# PI-run v0.2.2 Project Provider Expansion Report

Date: 2026-07-05 Asia/Taipei

Scope: expand the project-side PI-run orchestrator from `nats-only` to:

```text
nats-only -> wiremock-only -> jdbc-lightweight -> full-contract-baseline
```

The framework release jar remains unchanged. The project owns dependency startup, run workspace materialization, reporting, and cleanup.

## Implementation Paths

- Orchestrator: `pirun/run_contract_baseline.py`
- Docker wrapper: `pirun/docker_cli.py`
- NATS provisioner: `pirun/provisioners/nats.py`
- WireMock provisioner: `pirun/provisioners/wiremock.py`
- JDBC lightweight provisioner: `pirun/provisioners/jdbc.py`
- Materializers: `pirun/materialize/contract_baseline.py`
- Tests:
  - `tests/test_pirun_orchestrator.py`
  - `tests/test_pirun_wiremock.py`
  - `tests/test_pirun_jdbc.py`
  - `tests/test_pirun_materialize.py`

## Resource Policy

The implementation avoids large local DB containers.

```yaml
nats:
  image: nats:2.10-alpine
  memory_limit: 256m
wiremock:
  image: wiremock/wiremock:3.9.1
  memory_limit: 512m
jdbc-lightweight:
  provisioner: framework_embedded_h2
  external_container: false
framework_java:
  xmx: 512m
```

Oracle XE or similar heavy database containers were not started.

## Smoke Results

### nats-only

Command:

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode nats-only --run-id SMOKE-NATS-MATRIX-1
```

Result:

```yaml
project_provisioning_status: passed
materialization_status: passed
provider_runtime_invoked: true
framework_result:
  run_status: failed
  failure_codes:
    - NATS_CONNECTION_FAILED
  known_blocker: true
cleanup_status: passed
```

Evidence:

- `.pirun/runs/SMOKE-NATS-MATRIX-1/nats_capability/project_report.json`

Conclusion: project Docker NATS provisioning works. v0.2.2 still cannot consume `env://PIRUN_NATS_CONNECTION`.

### wiremock-only

Command:

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode wiremock-only --run-id SMOKE-WIREMOCK-2
```

Result:

```yaml
project_provisioning_status: passed
materialization_status: passed
framework_result:
  run_status: passed
  provider_runtime_invoked: true
cleanup_status: passed
```

Evidence:

- `.pirun/runs/SMOKE-WIREMOCK-2/wiremock_capability/project_report.json`
- `.pirun/runs/SMOKE-WIREMOCK-2/wiremock_capability/project_bindings/wiremock-payment-api.yaml`

Important limitation:

The project starts Docker WireMock and records the external `base_url`, but v0.2.2 WireMock provider contract rejects `base_url` as a binding key. Therefore the external URL is stored in project-owned `project_bindings/`, while the framework run still uses its embedded WireMock path.

### jdbc-lightweight

Command:

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode jdbc-lightweight --run-id SMOKE-JDBC-LIGHT-2
```

Result:

```yaml
project_provisioning_status: passed
materialization_status: passed
framework_result:
  exit_code: 0
  run_status: passed
  provider_runtime_invoked: true
cleanup_status: passed
```

Evidence:

- `.pirun/runs/SMOKE-JDBC-LIGHT-2/jdbc_capability/project_report.json`

Conclusion: lightweight JDBC is usable now through v0.2.2's embedded H2 provider capability path. This is intentionally not an Oracle XE substitute.

### full-contract-baseline

Command:

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode full-contract-baseline --run-id SMOKE-FULL-1
```

Result:

```yaml
project_provisioning_status: passed
materialization_status: passed
dependencies:
  - nats-event-bus
  - wiremock-payment-api
  - oracle-database
framework_result:
  run_status: blocked
  failure_codes:
    - CONTRACT_UNSUPPORTED_SUITE_RUNTIME
  known_blocker: true
cleanup_status: passed
```

Evidence:

- `.pirun/runs/SMOKE-FULL-1/contract_baseline/project_report.json`
- `.pirun/runs/SMOKE-FULL-1/contract_baseline/project_bindings/wiremock-payment-api.yaml`

Conclusion: the project can prepare all dependencies and artifacts for full baseline, but v0.2.2 still blocks mixed-provider suite runtime before provider dispatch.

## Current Capability Matrix

| Mode | Project provisioning | Framework run | Notes |
|---|---:|---:|---|
| `nats-only` | PASS | FAIL | External NATS secret ref not supported by v0.2.2. |
| `wiremock-only` | PASS | PASS | Framework uses embedded WireMock; project external URL is recorded separately. |
| `jdbc-lightweight` | PASS | PASS | Uses embedded H2, no heavy DB container. |
| `full-contract-baseline` | PASS | BLOCKED | Mixed provider suite runtime unsupported in v0.2.2. |

## Remaining Framework Fixes

1. Support external NATS `env://...` connection refs.
2. Support external/project-provisioned WireMock `base_url` or a `connect_mock` runtime operation.
3. Support mixed-provider `contract_baseline` runtime dispatch for `jdbc`, `nats`, and `wiremock_http_mock`.
4. Remove cwd coupling for provider contract registry resolution.
5. Honor project evidence policy in provider evidence output.
