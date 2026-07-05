# pi-run v0.2.3 Release Asset Check

Date: 2026-07-05

Status update: SUPERSEDED

`v0.2.3` release assets were published after this initial check. See `reports/pi-run-v0.2.3-report.md` for the final pi-run result.

## Scope

Check whether tag `v0.2.3` can be pi-run from release assets only.

Constraint: do not pull or use source code archives as pi-run inputs.

## Result

Status: BLOCKED

Reason: `v0.2.3` exists as a Git tag, but it is not available as a GitHub Release with framework release assets. The expanded assets page only exposes GitHub-generated source archives:

- `archive/refs/tags/v0.2.3.zip`
- `archive/refs/tags/v0.2.3.tar.gz`

The GitHub Releases API currently lists formal releases for `v0.2.2`, `v0.2.1`, and `v0.2.0`, but not `v0.2.3`.

## Evidence

Release page:

- `https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/tag/v0.2.3`

Expanded assets:

- `https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/expanded_assets/v0.2.3`

Observed expanded asset links:

```text
/hermanwangd/Auto_Regression_Test_Framework/archive/refs/tags/v0.2.3.zip
/hermanwangd/Auto_Regression_Test_Framework/archive/refs/tags/v0.2.3.tar.gz
```

GitHub Releases API summary:

```text
release_count 3
v0.2.2 Auto Regression Test Framework 0.2.2 17
v0.2.1 Auto Regression Test Framework 0.2.1 17
v0.2.0 Auto Regression Test Framework 0.2.0 14
```

Expected release binary URLs return 404:

```text
https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/download/v0.2.3/spec-driven-auto-regression-0.2.3.jar
https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/download/v0.2.3/bom.json
```

## pi-run Decision

Do not pi-run `v0.2.3` yet.

Using the source archive would violate the release-asset-only acceptance rule. Releasing the tag alone is not enough for pi-run validation.

## Required Release Assets

Publish a formal GitHub Release for `v0.2.3` with at least:

- `spec-driven-auto-regression-0.2.3.jar`
- usage-kit archive for `v0.2.3`
- SBOM / checksum / signature artifacts consistent with `v0.2.2`

After those assets exist, run the existing orchestrator sequence:

```text
nats-only -> wiremock-only -> jdbc-lightweight -> full-contract-baseline
```
