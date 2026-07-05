# pi-run v0.2.5 Release Check

Date: 2026-07-05 Asia/Taipei

Status: `RELEASE_FOUND_PI_RUN_EXECUTED`

Scope: release-asset-only precheck for `Auto_Regression_Test_Framework` v0.2.5. Source archives were not used.

## Result

`v0.2.5` is published and was pi-run from release assets only.

## Evidence

| Check | Result |
|---|---|
| `GET /repos/hermanwangd/Auto_Regression_Test_Framework/releases/tags/v0.2.5` | `200` |
| Published releases list | `v0.2.5`, `v0.2.4`, `v0.2.3`, `v0.2.2`, `v0.2.1`, `v0.2.0` |
| Tags list | `v0.2.5`, `v0.2.4`, `v0.2.3`, `v0.2.2`, `v0.2.1`, `v0.2.0` |
| Local `release-assets-v0.2.5` directory | present |
| Local `usage-kit-v0.2.5` directory | present |

Latest visible release:

| Tag | Published At | URL |
|---|---:|---|
| `v0.2.5` | `2026-07-05T14:52:46Z` | `https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/tag/v0.2.5` |

## Decision

pi-run execution was performed for v0.2.5. See `reports/pi-run-v0.2.5-goal-audit.md`.

Executed release-asset-only pipeline:

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
```

Runtime guardrail: Java heap was bounded with `-Xmx512m`; project-side Docker provisioning used NATS/WireMock lightweight containers only and did not use Oracle XE class containers.
