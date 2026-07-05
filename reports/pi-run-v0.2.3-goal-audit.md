# pi-run v0.2.3 Goal Audit

Date: 2026-07-05 Asia/Taipei

Status: Verified for the requested project-side pi-run acceptance gates. Framework-owned limitations are preserved as blocked or not-proven rows instead of being hidden.

## Evidence Index

- Release asset verification: `reports/pi-run-v0.2.3-release-asset-verification.md`
- Function coverage matrix: `reports/pi-run-v0.2.3-function-coverage-matrix.md`
- Runnable suite-mode matrix: `reports/pi-run-v0.2.3-full-coverage-report.md`
- Evidence/report command matrix: `reports/pi-run-v0.2.3-evidence-command-matrix.md`
- Project-mode pi-run report: `reports/pi-run-v0.2.3-report.md`
- Docker cleanup check: `reports/pi-run-v0.2.3-docker-cleanup-check.md`
- Raw secret scan: `reports/pi-run-v0.2.3-raw-secret-scan.md`

## Gate Status

| Gate | Current Status | Evidence |
|---|---:|---|
| Release asset checksum verification | PASS | Jar, usage-kit zip, BOM, and checksums asset verify against `checksums.sha256`. |
| Release asset signature verification | PASS | Detached signatures verify with release-provided certificate public keys. Certificate chain trust verification was not performed. |
| Source archive used | PASS | `source_archive_used: false`; release assets only. |
| Generated function coverage matrix | PASS | 35 provider/runtime rows generated from usage-kit registry/contracts/samples. |
| Runnable suite-mode matrix rows | PASS | 15 runnable suites executed `validate`, `run --dry-run`, and `run`; 45/45 commands passed. |
| Non-runnable rows have correct reason | PASS | All 21 blocked rows use `BLOCKED_*`: contract-only, deprecated-alias, or usage-kit-sample-gap. |
| Report positive cases | PASS | Supported text/yaml positive report cases pass. JSON format is separately `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT`. |
| Report negative cases | EXPECTED_FAIL | Supported text/yaml missing-evidence and secret-leak report cases fail as expected. JSON format is separately `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT`. |
| Validate-evidence positive cases | PASS | Valid result exits 0. |
| Validate-evidence negative cases | EXPECTED_FAIL | Missing evidence and secret leak exit 1 with owner-actionable findings. |
| Project-provisioned NATS consumption | PASS | `PIRUN-V023-NATS-2` project report shows `framework_runtime_executed`. |
| Project-provisioned WireMock external `base_url` consumption | NOT_PROVEN with framework issue | Project WireMock starts, but v0.2.3 framework evidence reports `external_base_url_not_consumed_by_framework_provider_capability`. |
| Lightweight JDBC execution | PASS | `PIRUN-V023-JDBC-2` project report shows `framework_runtime_executed`. |
| Kafka/IBM MQ native/ephemeral | BLOCKED_FRAMEWORK_CONTRACT_ONLY | Function matrix blocks native/ephemeral rows for Kafka and IBM MQ. |
| Command-capable providers without release samples | BLOCKED_USAGE_KIT_SAMPLE_GAP | Function matrix accounts for shell, external runner, Kubernetes, and VM runtime rows as usage-kit sample gaps. |
| Docker cleanup | PASS | Fresh Docker check for all final run IDs returns 0 leftover containers. |
| Raw secret scan | PASS | Generated reports and `.pirun/runs` evidence scan reports 0 findings. |

## Framework-owned Limitations Preserved

These do not block the project-side pi-run acceptance result because they are recorded as explicit framework issues:

- `report --format json` exits 2 in v0.2.3 and is recorded as `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT`.
- Project-provisioned external WireMock `base_url` is not proven consumed by the v0.2.3 framework runtime.
- Usage-kit sample gaps are blocked as `BLOCKED_USAGE_KIT_SAMPLE_GAP` rather than treated as runnable rows.

## Fresh Verification

```text
python3 pirun/verify_release_assets.py --framework-version 0.2.3 --output-dir reports
checksum_verification: PASS
signature_verification: PASS

python3 pirun/inspect_usage_kit.py --framework-version 0.2.3 --output-dir reports
matrix_row_count: 35

python3 pirun/run_usage_kit_matrix.py --framework-version 0.2.3 --matrix-json reports/pi-run-v0.2.3-function-coverage-matrix.json --output-dir reports --command-set 'validate,run --dry-run,run' --execute
planned_suite_count: 15
unexpected_failures: 0

python3 pirun/run_evidence_matrix.py --framework-version 0.2.3 --output-dir reports
unexpected_fail_count: 0
blocked_framework_count: 3
report_supported_positive_missing_formats: none
report_supported_negative_missing_formats: none

python3 -m unittest discover -s tests
Ran 45 tests in 4.162s
OK

python3 -m compileall -q pirun
OK

python3 pirun/scan_raw_secrets.py --framework-version 0.2.3 --output-dir reports reports .pirun/runs
raw_secret_scan: PASS
finding_count: 0

/usr/local/bin/docker ps checks for final run IDs
PIRUN-V023-NATS-2 0
PIRUN-V023-WIREMOCK-3 0
PIRUN-V023-JDBC-2 0
PIRUN-V023-FULL-4 0
```
