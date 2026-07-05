# PI-run v0.2.2 Project-Provisioned NATS POC Report

Date: 2026-07-04 Asia/Taipei

Scope: verify whether a PI-run project can provision a Docker NATS runtime, materialize standard framework artifacts, invoke the v0.2.2 release jar unchanged, and collect cleanup/provisioning evidence.

## Command

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode nats-only --run-id SMOKE-NATS-PROJECT-3
```

The command intentionally exits non-zero when the framework run fails. The project report is still written in `finally`.

## Result

Project-owned runtime provisioning passed.

```yaml
project_provisioning_status: passed
materialization_status: passed
framework_invoked: true
cleanup_status: passed
```

Framework execution reached the NATS provider runtime, but failed on external secret-ref consumption:

```yaml
run_status: failed
provider_runtime_invoked: true
provider_type: nats
runtime_mode: ephemeral
failure_codes:
  - NATS_CONNECTION_FAILED
failure_reason: Secret-ref backed NATS connection is not available in local provider capability mode.
```

This proves the project can start and pass a Docker NATS endpoint into the framework artifacts, but v0.2.2 cannot yet consume that endpoint for the NATS provider capability runtime.

## Evidence Paths

- Project report: `.pirun/runs/SMOKE-NATS-PROJECT-3/nats_capability/project_report.json`
- Project provisioning evidence: `.pirun/runs/SMOKE-NATS-PROJECT-3/nats_capability/provisioning_evidence.yaml`
- Materialized environment binding: `.pirun/runs/SMOKE-NATS-PROJECT-3/nats_capability/environment_bindings/ci.yaml`
- Framework stdout capture: `.pirun/runs/SMOKE-NATS-PROJECT-3/nats_capability/framework_stdout.txt`
- Framework result JSON: `usage-kit-v0.2.2/usage-kit/target/provider-capability/nats/NATS-CAPABILITY-v0.2/BATCH-NATS-20260704155631102-1/RUN-NATS-20260704155631102-1/result.json`
- Failure evidence: `usage-kit-v0.2.2/usage-kit/target/provider-capability/nats/NATS-CAPABILITY-v0.2/BATCH-NATS-20260704155631102-1/RUN-NATS-20260704155631102-1/provider-evidence/nats/failure_detail.yaml`

## Implementation Paths

- Docker CLI wrapper: `pirun/docker_cli.py`
- NATS provisioner: `pirun/provisioners/nats.py`
- NATS materializer: `pirun/materialize/contract_baseline.py`
- Orchestrator: `pirun/run_contract_baseline.py`
- Unit tests:
  - `tests/test_pirun_docker_cli.py`
  - `tests/test_pirun_nats.py`
  - `tests/test_pirun_materialize.py`

## Key Findings

### FWK-P0-001: External NATS secret_ref is not supported

Evidence:

```yaml
failure_code: NATS_CONNECTION_FAILED
reason: Secret-ref backed NATS connection is not available in local provider capability mode.
owner_action: Run this capability sample with an approved local_ref or provide an environment-specific NATS runtime.
```

Impact:

- A project can provision Docker NATS and materialize `env://PIRUN_NATS_CONNECTION`.
- v0.2.2 cannot use that connection in the NATS provider runtime.
- Therefore project-side Testcontainers/Docker provisioning alone cannot produce full external NATS runtime acceptance evidence until framework support is added.

Recommended framework fix:

- Resolve `env://...` secret refs for NATS connection values.
- For `runtime_mode: ephemeral` and `native`, use an actual NATS client instead of the current in-memory provider-capability path.
- Keep `approved_local_ref` only for framework-owned mock/local capability runs.

### FWK-P0-002: Provider registry resolution depends on framework cwd

Control result:

- Running the copied NATS suite from repo root returned `CONTRACT_UNKNOWN_PROVIDER_TYPE`.
- Running the same copied suite with cwd `usage-kit-v0.2.2/usage-kit` passed provider type resolution.

Impact:

- Project materialized suites outside the usage-kit root are not portable unless the runner sets cwd to the usage-kit root.
- This is a framework integration hazard because provider capability support should not depend on shell cwd.

Recommended framework fix:

- Bundle provider capability registry/contracts into the jar, or expose `--contract-root <path>`.
- Resolve provider types independent of process cwd.
- Include the resolved contract root in run diagnostics.

### FWK-P1-001: Failed run stdout omits failure_code

The failed framework stdout showed `run_status: failed` and `findings: []`, while `NATS_CONNECTION_FAILED` appeared only in `result.json` and provider evidence.

Recommended framework fix:

- Include top-level `failure_code`, `failure_reason`, and `owner_action` in stdout for failed provider runtime execution.

### FWK-P1-002: Evidence classification is inconsistent

Materialized suite/test labels use:

```yaml
evidence_classification: local_ci_ephemeral_only
downstream_release_evidence: false
```

But framework stdout and provider evidence still show:

```yaml
evidence_classification: framework_provider_capability_only
```

Recommended framework fix:

- Make runtime evidence classification honor suite/test/evidence policy after project materialization.

## Project-Side Conclusion

The project-side NATS provisioning POC is valid for proving Docker lifecycle, endpoint materialization, report generation, and cleanup. It is not full framework acceptance evidence because v0.2.2 blocks external NATS consumption with `NATS_CONNECTION_FAILED`.

Until the framework is fixed, the project should keep:

- Docker lifecycle outside the framework.
- Materialized artifacts under `.pirun/runs/<run_id>/...`.
- Framework invocation cwd set to `usage-kit-v0.2.2/usage-kit`.
- Report parsing from `result.json`, not stdout only.
