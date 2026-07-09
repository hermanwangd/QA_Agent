# pi-run v0.2.5 Goal Audit

Date: 2026-07-05 Asia/Taipei

Status: Verified for release-asset-only project-side pi-run. Framework-owned limitations remain as explicit blocked/not-proven rows.

## Evidence Artifacts

- Release check: `reports/pi-run-v0.2.5-release-check.md`
- Release asset verification: `reports/pi-run-v0.2.5-release-asset-verification.md`
- Function coverage matrix: `reports/pi-run-v0.2.5-function-coverage-matrix.md`
- Runnable suite-mode matrix: `reports/pi-run-v0.2.5-full-coverage-report.md`
- Evidence/report command matrix: `reports/pi-run-v0.2.5-evidence-command-matrix.md`
- Docker cleanup check: `reports/pi-run-v0.2.5-docker-cleanup-check.md`
- Raw secret scan: `reports/pi-run-v0.2.5-raw-secret-scan.md`
- Heavy JDBC Testcontainers check: `reports/pi-run-v0.2.5-testcontainers-heavy-jdbc-report.md`

## Acceptance Summary

| Gate | Status | Evidence |
|---|---:|---|
| Release `v0.2.5` exists | `PASS` | GitHub release API returned `200`; published at `2026-07-05T14:52:46Z`. |
| Source archive avoided | `PASS` | `source_archive_used: false`; only release assets were downloaded and used. |
| Release checksum verification | `PASS` | Jar, usage-kit zip, BOM, and checksum asset verify against `checksums.sha256`. |
| Release detached signature verification | `PASS_WITH_LIMITATION` | Raw signatures verify with release-provided certificate public keys; certificate chain trust verification was not performed. |
| Usage-kit function coverage matrix generated | `PASS` | 18 registry providers, 18 provider contracts, 37 provider/runtime rows. |
| Registry/contract consistency | `PASS` | No registry-without-contract rows and no contract-without-registry rows. |
| Runnable suite-mode matrix | `PASS` | 36 suites, 108 commands executed, 0 unexpected failures. |
| Evidence command matrix | `PASS_WITH_FRAMEWORK_BLOCKS` | 12 cases; 3 PASS, 6 EXPECTED_FAIL, 3 framework-blocked JSON report cases, 0 unexpected failures. |
| Project-provisioned NATS | `PASS` | `PIRUN-V025-NATS-1` executed with `framework_runtime_executed`. |
| Project-provisioned WireMock external `base_url` | `NOT_PROVEN_WITH_FRAMEWORK_ISSUE` | Project WireMock starts and framework run passes, but external `base_url` is still not consumed by framework capability runtime. |
| Lightweight JDBC | `PASS` | `PIRUN-V025-JDBC-1` executed with `framework_runtime_executed`; no Oracle XE class container used. |
| Project-provisioned Oracle/DB2 heavy JDBC | `NOT_PROVEN_WITH_FRAMEWORK_ISSUE` | Oracle and DB2 Testcontainers reached framework invocation, but both failed with `SECRET_RESOLUTION_ERROR` for `env://JDBC_CONNECTION`. |
| Full contract baseline | `PASS_WITH_WIREMOCK_LIMITATION` | NATS and JDBC consumed; WireMock external `base_url` still not consumed. |
| Docker cleanup | `PASS` | 0 leftover containers for all final v0.2.5 run IDs. |
| Raw secret scan | `PASS` | 766 files scanned, 0 findings. |

## Function Coverage Summary

| Status | Count | Meaning |
|---|---:|---|
| `PASS` | 23 | Runnable release usage-kit rows were executed through suite-mode. |
| `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | 11 | Provider/runtime rows are explicitly contract-only in this release. |
| `BLOCKED_DEPRECATED_ALIAS` | 3 | `kafka_messaging/*` remains a deprecated compatibility alias. |
| `BLOCKED_USAGE_KIT_SAMPLE_GAP` | 0 | No supported provider/runtime rows are missing release usage-kit samples. |

## v0.2.5 Improvements Over v0.2.4

- Supported sample gaps are closed: `grpc_client/mock`, `grpc_client/stub`, `polling_observer/ephemeral`, `rest_client/mock`, and `rest_client/stub` are now runnable and passed suite-mode verification.
- PASS provider/runtime rows increased from 18 to 23.
- Release usage-kit sample suites increased from 20 to 40 because v0.2.5 includes both new categorized sample paths and compatibility sample paths.
- Runnable suite matrix increased from 54 commands in v0.2.4 to 108 commands across 36 unique suite manifests.

## Remaining Framework Issues

These do not block the project-side pi-run result because they are recorded as explicit framework limitations:

- Release verification docs still miss `report` and `validate-evidence` commands.
- `report --format json` still exits `2` and is recorded as `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT`.
- Project-provisioned WireMock external `base_url` still is not consumed by framework runtime evidence.
- Project-provisioned Oracle/DB2 JDBC external `env://JDBC_CONNECTION` is not resolved by framework provider capability runtime.
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
- 3 provider/runtime rows remain `BLOCKED_DEPRECATED_ALIAS`:
  - `kafka_messaging/ephemeral`
  - `kafka_messaging/mock`
  - `kafka_messaging/native`

## Commands

```text
python3 pirun/verify_release_assets.py --framework-version 0.2.5 --output-dir reports
python3 pirun/inspect_usage_kit.py --framework-version 0.2.5 --output-dir reports
python3 pirun/run_usage_kit_matrix.py --framework-version 0.2.5 --matrix-json reports/pi-run-v0.2.5-function-coverage-matrix.json --output-dir reports --command-set 'validate,run --dry-run,run' --execute
python3 pirun/run_evidence_matrix.py --framework-version 0.2.5 --output-dir reports
python3 pirun/run_contract_baseline.py --framework-version 0.2.5 --profile ci --mode nats-only --run-id PIRUN-V025-NATS-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.5 --profile ci --mode wiremock-only --run-id PIRUN-V025-WIREMOCK-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.5 --profile ci --mode jdbc-lightweight --run-id PIRUN-V025-JDBC-1
python3 pirun/run_contract_baseline.py --framework-version 0.2.5 --profile ci --mode full-contract-baseline --run-id PIRUN-V025-FULL-1
python3 pirun/scan_raw_secrets.py --framework-version 0.2.5 --output-dir reports reports .pirun/runs
PATH="/Applications/Docker.app/Contents/Resources/bin:/usr/local/bin:/opt/homebrew/bin:$PATH" PIRUN_ENABLE_TESTCONTAINERS_HEAVY_JDBC=1 PIRUN_ENABLE_DB2_TESTCONTAINER=1 PIRUN_ACCEPT_DB2_LICENSE=1 PIRUN_ALLOW_PRIVILEGED_DB2=1 PIRUN_FRAMEWORK_VERSION=0.2.5 MAVEN_OPTS="-Xmx1024m" ./mvnw -Dtest=HeavyJdbcProviderTestcontainersIT#db2ContainerMustBeConsumedByFrameworkJdbcProvider test
```
