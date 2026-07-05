# pi-run v0.2.4 Goal Audit

Date: 2026-07-05 Asia/Taipei

Status: Verified for release-asset-only project-side pi-run. Framework-owned limitations remain as explicit blocked/not-proven rows.

## Evidence Artifacts

- Release check: `reports/pi-run-v0.2.4-release-check.md`
- Release asset verification: `reports/pi-run-v0.2.4-release-asset-verification.md`
- Function coverage matrix: `reports/pi-run-v0.2.4-function-coverage-matrix.md`
- Runnable suite-mode matrix: `reports/pi-run-v0.2.4-full-coverage-report.md`
- Evidence/report command matrix: `reports/pi-run-v0.2.4-evidence-command-matrix.md`
- Docker cleanup check: `reports/pi-run-v0.2.4-docker-cleanup-check.md`
- Raw secret scan: `reports/pi-run-v0.2.4-raw-secret-scan.md`

## Acceptance Summary

| Gate | Status | Evidence |
|---|---:|---|
| Release `v0.2.4` exists | `PASS` | GitHub release API returned `200`; published at `2026-07-05T12:57:06Z`. |
| Source archive avoided | `PASS` | `source_archive_used: false`; only release assets were downloaded and used. |
| Release checksum verification | `PASS` | Jar, usage-kit zip, BOM, and checksum asset verify against `checksums.sha256`. |
| Release detached signature verification | `PASS_WITH_LIMITATION` | Raw signatures verify with release-provided certificate public keys; certificate chain trust verification was not performed. |
| Usage-kit function coverage matrix generated | `PASS` | 18 registry providers, 18 provider contracts, 37 provider/runtime rows. |
| Registry/contract consistency | `PASS` | No registry-without-contract rows and no contract-without-registry rows. |
| Runnable suite-mode matrix | `PASS` | 18 suites, 54 commands executed, 0 unexpected failures. |
| Evidence command matrix | `PASS_WITH_FRAMEWORK_BLOCKS` | 12 cases; 3 PASS, 6 EXPECTED_FAIL, 3 framework-blocked JSON report cases, 0 unexpected failures. |
| Project-provisioned NATS | `PASS` | `PIRUN-V024-NATS-1` executed with `framework_runtime_executed`. |
| Project-provisioned WireMock external `base_url` | `NOT_PROVEN_WITH_FRAMEWORK_ISSUE` | Project WireMock starts and framework run passes, but external `base_url` is still not consumed by framework capability runtime. |
| Lightweight JDBC | `PASS` | `PIRUN-V024-JDBC-1` executed with `framework_runtime_executed`; no Oracle XE class container used. |
| Full contract baseline | `PASS_WITH_WIREMOCK_LIMITATION` | NATS and JDBC consumed; WireMock external `base_url` still not consumed. |
| Docker cleanup | `PASS` | 0 leftover containers for all final v0.2.4 run IDs. |
| Raw secret scan | `PASS` | 610 files scanned, 0 findings. |

## Function Coverage Summary

| Status | Count | Meaning |
|---|---:|---|
| `PASS` | 18 | Runnable release usage-kit rows were executed through suite-mode. |
| `BLOCKED_USAGE_KIT_SAMPLE_GAP` | 5 | Supported provider/runtime rows exist, but the release usage-kit has no executable sample for that row. |
| `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | 11 | Provider/runtime rows are explicitly contract-only in this release. |
| `BLOCKED_DEPRECATED_ALIAS` | 3 | `kafka_messaging/*` remains a deprecated compatibility alias. |

## v0.2.4 Improvements Over v0.2.3

- `kafka/native` is now runnable and passed suite-mode verification.
- `ibm_mq/native` is now runnable and passed suite-mode verification.
- Matrix row count increased from 35 to 37 because v0.2.4 adds provider rows for `common_verify` and `sample_fake_provider`.
- Runnable suite count increased from 15 to 18.
- Executed command count increased from 45 to 54.

## Remaining Framework Issues

These do not block the project-side pi-run result because they are recorded as explicit framework limitations:

- Release verification docs still miss `report` and `validate-evidence` commands.
- `report --format json` still exits `2` and is recorded as `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT`.
- Project-provisioned WireMock external `base_url` still is not consumed by framework runtime evidence.
- 11 provider/runtime rows remain `BLOCKED_FRAMEWORK_CONTRACT_ONLY`:
  - `external_runner/native`
  - `external_runner/stub`
  - `ibm_mq/ephemeral`
  - `kafka/ephemeral`
  - `kubernetes_runtime/mock`
  - `kubernetes_runtime/native`
  - `shell_command/mock`
  - `shell_command/native`
  - `shell_command/stub`
  - `vm_runtime/mock`
  - `vm_runtime/native`
- 5 supported provider/runtime rows still have `BLOCKED_USAGE_KIT_SAMPLE_GAP`:
  - `grpc_client/mock`
  - `grpc_client/stub`
  - `polling_observer/ephemeral`
  - `rest_client/mock`
  - `rest_client/stub`

## Commands

```text
python3 pirun/verify_release_assets.py --framework-version 0.2.4 --output-dir reports
python3 pirun/inspect_usage_kit.py --framework-version 0.2.4 --output-dir reports
python3 pirun/run_usage_kit_matrix.py --framework-version 0.2.4 --matrix-json reports/pi-run-v0.2.4-function-coverage-matrix.json --output-dir reports --command-set 'validate,run --dry-run,run' --execute
python3 pirun/run_evidence_matrix.py --framework-version 0.2.4 --output-dir reports
python3 pirun/run_contract_baseline.py --framework-version 0.2.4 --profile ci --mode nats-only --run-id PIRUN-V024-NATS-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.4 --profile ci --mode wiremock-only --run-id PIRUN-V024-WIREMOCK-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.4 --profile ci --mode jdbc-lightweight --run-id PIRUN-V024-JDBC-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.4 --profile ci --mode full-contract-baseline --run-id PIRUN-V024-FULL-1
python3 pirun/scan_raw_secrets.py --framework-version 0.2.4 --output-dir reports reports .pirun/runs
```
