# pi-run v0.2.3 Report

Date: 2026-07-05

## Scope

Validate `v0.2.3` from GitHub release assets only. Source archives were not used.

Modes:

```text
nats-only -> wiremock-only -> jdbc-lightweight -> full-contract-baseline
```

## Release Assets

Downloaded assets:

- `release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar`
- `usage-kit-v0.2.3/usage-kit`
- `release-assets-v0.2.3/checksums.sha256`
- `release-assets-v0.2.3/*.sig`
- `release-assets-v0.2.3/*.pem`
- `release-assets-v0.2.3/bom.json`
- `release-assets-v0.2.3/bom.xml`

Checksum verification:

```text
d9a0a672be58efa8ffa0aeebed1af0b2b4a8a686a00ffe94cfaa30368ca24175  spec-driven-auto-regression-0.2.3.jar
89b540af54f01c136d68e7ba728241ed66a0355e9a8cbf0d88bce327917d815d  spec-driven-auto-regression-0.2.3-usage-kit.zip
```

The values matched `checksums.sha256`.

Signature verification:

```text
checksum_verification: PASS
signature_verification: PASS
source_archive_used: false
```

## Harness Update

The pi-run harness now supports:

```text
--framework-version 0.2.3
```

This selects:

- `release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar`
- `usage-kit-v0.2.3/usage-kit`
- `usage-kit-v0.2.3/usage-kit/samples`

## Result Matrix

| Mode | Run ID | Project provisioning | Framework run | Provider runtime | Cleanup | Result |
|---|---|---:|---:|---:|---:|---:|
| `nats-only` | `PIRUN-V023-NATS-2` | PASS | PASS | PASS | PASS | PASS |
| `wiremock-only` | `PIRUN-V023-WIREMOCK-3` | PASS | PASS | PASS | PASS | PASS with caveat |
| `jdbc-lightweight` | `PIRUN-V023-JDBC-2` | PASS | PASS | PASS | PASS | PASS |
| `full-contract-baseline` | `PIRUN-V023-FULL-4` | PASS | PASS | PASS | PASS | PASS with caveat |

All four final runs exited with code `0`.

## Evidence Paths

- `.pirun/runs/PIRUN-V023-NATS-2/nats_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-WIREMOCK-3/wiremock_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-JDBC-2/jdbc_capability/project_report.json`
- `.pirun/runs/PIRUN-V023-FULL-4/contract_baseline/project_report.json`

Docker cleanup check:

```text
PIRUN-V023-NATS-2 0
PIRUN-V023-WIREMOCK-3 0
PIRUN-V023-JDBC-2 0
PIRUN-V023-FULL-4 0
```

## Key Findings

### Improved Since v0.2.2

`nats-only` now passes with project-provisioned Docker NATS:

```text
provider_id: local-nats-event-bus
provider_type: nats
framework_consumed: true
framework_consumption_status: framework_runtime_executed
```

`full-contract-baseline` now passes mixed-provider runtime:

```text
provider_types: wiremock_http_mock,jdbc,nats
provider_ids: wiremock-payment-api,oracle-database,nats-event-bus
run_status: passed
```

This removes the v0.2.2 blocker `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`.

### Remaining Caveat

Project Docker WireMock starts successfully, but its external `base_url` is not consumed by the framework provider capability runtime.

Evidence:

```text
framework_consumption_status: external_base_url_not_consumed_by_framework_provider_capability
```

In `full-contract-baseline`, the framework executed the WireMock provider runtime and passed the WireMock steps, but evidence shows the runtime used a framework-managed localhost WireMock endpoint, not the project Docker WireMock `base_url`.

Therefore:

- Mixed-provider framework runtime: PASS
- Project-provisioned external NATS consumption: PASS
- Framework embedded H2 JDBC consumption: PASS
- Project-provisioned external WireMock consumption: NOT YET PROVEN

## Full Function Coverage

Generated coverage matrix:

- `reports/pi-run-v0.2.3-function-coverage-matrix.md`
- 35 provider/runtime rows
- 15 runnable suites
- 21 blocked rows with explicit `BLOCKED_*` statuses

Runnable suite-mode matrix:

```text
planned_suite_count: 15
planned_command_count: 45
executed_command_count: 45
unexpected_failures: 0
```

Evidence/report command matrix:

```text
report_supported_positive_status: PASS
report_supported_positive_missing_formats: none
report_supported_negative_status: EXPECTED_FAIL
report_supported_negative_missing_formats: none
validate_evidence_positive_status: PASS
validate_evidence_negative_status: EXPECTED_FAIL
blocked_framework_count: 3
```

The three framework-blocked probes are `report --format json`, which exits `2` in v0.2.3 with unsupported format.

## Verification

Commands:

```sh
python3 pirun/verify_release_assets.py --framework-version 0.2.3 --output-dir reports
python3 pirun/inspect_usage_kit.py --framework-version 0.2.3 --output-dir reports
python3 pirun/run_usage_kit_matrix.py --framework-version 0.2.3 --matrix-json reports/pi-run-v0.2.3-function-coverage-matrix.json --output-dir reports --command-set 'validate,run --dry-run,run' --execute
python3 pirun/run_evidence_matrix.py --framework-version 0.2.3 --output-dir reports
python3 pirun/scan_raw_secrets.py --framework-version 0.2.3 --output-dir reports reports .pirun/runs
python3 -m unittest discover -s tests
python3 -m compileall -q pirun

python3 pirun/run_contract_baseline.py --framework-version 0.2.3 --profile ci --mode nats-only --run-id PIRUN-V023-NATS-2
python3 pirun/run_contract_baseline.py --framework-version 0.2.3 --profile ci --mode wiremock-only --run-id PIRUN-V023-WIREMOCK-3
python3 pirun/run_contract_baseline.py --framework-version 0.2.3 --profile ci --mode jdbc-lightweight --run-id PIRUN-V023-JDBC-2
python3 pirun/run_contract_baseline.py --framework-version 0.2.3 --profile ci --mode full-contract-baseline --run-id PIRUN-V023-FULL-4
```

Unit verification:

```text
Ran 45 tests - OK
compileall - OK
raw_secret_scan: PASS
finding_count: 0
```

Review hardening added after code review:

- Raw secret scan now catches common JSON/YAML key-value secret shapes, not only simple password assignments.
- Captured framework stdout/stderr are redacted before being written into project reports.
- NATS/JDBC consumption proof now requires matching framework-reported `provider_id` and `provider_type`.
- Report gate summaries now fail if required supported text/yaml formats are missing.
- Safety-policy blocking was removed from project-side function coverage classification; command-capable rows without executable release samples are now usage-kit sample gaps.

## Final Assessment

`v0.2.3` is pi-run accepted for the current project-side matrix, with one explicit limitation:

The framework still needs a contract for consuming a project-provisioned external WireMock `base_url`.
