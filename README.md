# test_framework_pirun

Release-asset-only PI-run workspace for the Auto Regression Test Framework.

## Layout

- `pirun/`: project-side PI-run orchestration, release verification, usage-kit inspection, and evidence helpers.
- `tests/`: lightweight regression tests for the PI-run harness.
- `reports/`: generated acceptance reports and proposal documents that are useful to review.
- `docs/`: supporting plans, architecture notes, and release-package evidence.
- `dummy_app/` and `pi_run_demo/`: local dummy application material used by framework acceptance.
- `tools/`: one-off or version-specific PI-run utilities.
- `skills/`: repo-local Codex skills for using this test framework.
- `.pirun/runs/`: local runtime output for orchestrated PI-runs.
- `artifacts/`: ignored local cache for downloaded or generated assets.

## Artifact Cache

Keep bulky release and generated files under `artifacts/`:

- `artifacts/release-assets/release-assets-v<version>/`
- `artifacts/usage-kits/usage-kit-v<version>/usage-kit/`
- `artifacts/jar-inspect/`
- `artifacts/acceptance-workspaces/`
- `artifacts/target/`

The PI-run helpers prefer this layout and still fall back to the old top-level `release-assets-v*` and `usage-kit-v*` paths for compatibility.

## Common Checks

```bash
python3 -m unittest discover -s tests
python3 pirun/verify_release_assets.py --framework-version 0.2.5 --output-dir reports
python3 pirun/inspect_usage_kit.py --framework-version 0.2.5 --output-dir reports
```

## Key Reports

- `reports/pi-run-heavy-jdbc-container-proposal.md`: isolated Oracle/DB2 JDBC container PI-run proposal with resource gates, runtime boundary, and framework-consumption evidence rules.

## Heavy JDBC Container PI-run

Oracle and DB2 container runs are manual opt-in checks. They are not part of the default unit test suite or `full-contract-baseline`, and provisioning is owned by this PI-run project rather than the framework jar.

Acceptance `PASS` means the released framework JDBC provider consumed the external JDBC binding and executed successfully. If the DB container starts but framework JDBC consumption is not proven, the run is reported as `PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN` and exits non-zero.

Oracle:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ORACLE_IMAGE=gvenzl/oracle-free:23-slim-faststart \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db oracle --framework-version 0.2.5
```

DB2:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ACCEPT_DB2_LICENSE=1 \
PIRUN_ALLOW_PRIVILEGED_DB2=1 \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db db2 --framework-version 0.2.5
```

On an 8 GB local machine, run only Oracle after Docker has at least 4 GB available. Run DB2 on a dedicated runner with at least 16 GB host RAM and Docker memory configured to 8 GB or more.
