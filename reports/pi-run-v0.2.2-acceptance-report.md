# PI-run v0.2.2 Acceptance Report

Date: 2026-07-04 Asia/Taipei

Scope: GitHub release assets for `Auto_Regression_Test_Framework` v0.2.2 only. No source checkout was used.

Release source:

- https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/tag/v0.2.2

Tested assets:

- `release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar`
- `release-assets-v0.2.2/spec-driven-auto-regression-0.2.2-usage-kit.zip`
- `release-assets-v0.2.2/bom.json`
- `release-assets-v0.2.2/bom.xml`
- `release-assets-v0.2.2/dependency-check-report.json`

All Java commands were run with `-Xmx512m` to stay below the local 8G memory safety limit.

## Verdict

v0.2.2 is a major improvement over v0.2.1, but it is not fully green as a complete custom-application PI-run.

Accepted as passing:

- Release asset checksum and version identity.
- CLI help/no-command behavior and the new `pi-run` alias.
- Suite-mode full execution of the local dummy REST application.
- Suite-mode parent provider capability dispatch: 12/12 child suites passed.
- Mock server cross verification: 6/6 passed, including 3 expected-failure cases.
- Golden E2E, evidence hardening, YAML report output, profile validation consistency, RP-mode deprecation, and dependency-check triage.

Remaining blocker:

- The custom native REST suite full run passes and `validate-evidence` passes, but `report --format yaml` rejects the result with `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`.
- The result has `labels.evidence_classification: framework_provider_capability_only` and `labels.downstream_release_evidence: false`, but the generated `provider_results[0].release_evidence_eligible` is `true`.
- This makes the custom app PI-run execution usable, but the custom app PI-run reporting path is still not acceptably complete.

## Release Asset Integrity

Local SHA-256 values matched `release-assets-v0.2.2/checksums.sha256`:

| Asset | SHA-256 |
|---|---|
| `spec-driven-auto-regression-0.2.2.jar` | `335fb4a218020f14ff60d28a3762b0bc1cb194f1d9974e0390b7a67aef114fb1` |
| `spec-driven-auto-regression-0.2.2-usage-kit.zip` | `93f0fb00bcea44a4e87eab35205f11814b4ee0fbd5c319a405e27106d84ea493` |
| `bom.json` | `06d31526d3cf54f759e68d7bef5dcacf4760bf67d8c9e6b39196c4fb9a475959` |
| `bom.xml` | `8c3cbf906bf300f82bf2c88f5e720f02a5d1124411ebcfea9a5747eec29587cb` |

Jar manifest:

- `Implementation-Version: 0.2.2`
- `Spring-Boot-Version: 3.5.16`

## CLI Surface

`--help` now returns usage successfully:

```text
usage: regress <command> [options]
commands:
  validate --suite <suite_manifest> [--profile <profile>]
  run --suite <suite_manifest> --profile <profile>
  run --suite <suite_manifest> --dry-run [--profile <profile>]
  pi-run --suite <suite_manifest> --profile <profile>
  report --result <result_json> [--format text|yaml]
  validate-evidence --result <result_json>
```

No-command invocation also prints usage instead of surfacing the v0.2.1 Spring startup error.

RP-mode is now hard-deprecated for current PI-run:

```text
run_status: blocked
failure_code: LEGACY_RP_MODE_DEPRECATED
owner_action: Use run --suite <suite_manifest> --profile <profile>.
```

## Dummy REST Custom Application

Local dummy service:

- `dummy_app/app.py`
- `tests/test_dummy_app.py`
- PI-run suite: `pi_run_demo/dummy_rest/suite_manifest.yaml`

Covered endpoints:

- `GET /health`
- `POST /orders`
- `GET /orders/{id}`

### Suite Validation

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar validate \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy
```

Observed:

```yaml
validation_status: passed
suite_id: DUMMY-REST-PI-RUN-v0.2
provider_types_used:
  - rest_client
findings: []
```

### PI-run Dry Run

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar pi-run \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy \
  --dry-run
```

Observed:

```yaml
run_status: dry_run_ready
provider_runtime_invoked: false
provider_type: rest_client
runtime_mode: native
findings: []
```

### PI-run Full Run

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar pi-run \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy
```

Observed:

```yaml
run_status: passed
suite_id: DUMMY-REST-PI-RUN-v0.2
batch_id: BATCH-REST-20260704141208275-1
run_id: RUN-REST-20260704141208275-1
test_count: 1
passed_count: 1
failed_count: 0
provider_runtime_executed: true
provider_type: rest_client
provider_id: dummy-order-api
```

Result evidence:

- `target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141208275-1/RUN-REST-20260704141208275-1/result.json`
- `target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141208275-1/RUN-REST-20260704141208275-1/evidence_index.yaml`

### Evidence Validation

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar validate-evidence \
  --result target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141208275-1/RUN-REST-20260704141208275-1/result.json
```

Observed:

```yaml
evidence_validation_status: passed
missing_evidence_count: 0
failed_evidence_count: 0
masking_status: passed
findings: []
```

### Report Gate Blocker

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar report \
  --result target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141208275-1/RUN-REST-20260704141208275-1/result.json \
  --format yaml
```

Observed:

```yaml
report_status: invalid
findings:
  - field_path: provider_results.release_evidence_eligible
    reason: mock_release_evidence_claim
    failure_code: VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM
    owner_action: Mark contract-baseline provider results as framework evidence only.
```

Relevant result fields:

```json
{
  "labels": {
    "evidence_classification": "framework_provider_capability_only",
    "downstream_release_evidence": false
  },
  "provider_results": [
    {
      "provider_type": "rest_client",
      "runtime_mode": "native",
      "status": "passed",
      "release_evidence_eligible": true
    }
  ]
}
```

Impact: users can run a custom native REST suite, but cannot get a clean review-ready report for the same run when the suite is marked framework-only/non-downstream release evidence.

Suggested fix:

- Make result generation set `provider_results[].release_evidence_eligible: false` when the suite labels or evidence policy say `downstream_release_evidence: false` or `framework_provider_capability_only`.
- Alternatively, if native `rest_client` with owner bindings is intended to be release-evidence eligible, the report validator must not classify that result as `mock_release_evidence_claim`.
- Add a regression test where the same custom REST result passes `validate-evidence` and `report --format yaml`.

Acceptance criterion:

```yaml
report_status: review_ready
release_evidence_eligible: false
missing_evidence_count: 0
masking_status: passed
findings: []
```

## Provider Capability Parent Suite

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/suite_manifest.yaml \
  --profile local_provider
```

Observed:

```yaml
run_status: passed
suite_id: PROVIDER-CAPABILITY-P0-v0.2
batch_id: BATCH-MR6FWCOC
run_id: RUN-1b7a5655-9e4d-4404-b069-3afea99689b9
test_count: 12
passed_count: 12
failed_count: 0
expected_failure_count: 0
unsupported_count: 0
blocked_count: 0
```

Evidence:

- `usage-kit-v0.2.2/usage-kit/target/suite-groups/PROVIDER-CAPABILITY-P0-v0.2/BATCH-MR6FWCOC/RUN-1b7a5655-9e4d-4404-b069-3afea99689b9/suite_summary.yaml`

Covered child suites:

- `wiremock`
- `wiremock_http_request`
- `jdbc`
- `nats`
- `common_verify`
- `compare`
- `polling`
- `soap_mock`
- `grpc_mock`
- `kafka`
- `ibm_mq`
- `messaging_mixed`

This closes the v0.2.1 parent-suite dispatch blocker.

## Mock Server Cross Verification

Command:

```sh
java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/mock_server_cross_verify/suite_manifest.yaml \
  --profile local_mock_server_cross_verify
```

Observed:

```yaml
run_status: passed
suite_id: MOCK-SERVER-CROSS-VERIFY-v0.2
batch_id: BATCH-MR6FWKVN
run_id: RUN-3892e93a-4521-48ec-8df2-5e834f7b5927
test_count: 6
passed_count: 6
failed_count: 0
expected_failure_count: 3
expected_failed_observed_count: 3
unsupported_count: 0
blocked_count: 0
```

Evidence:

- `usage-kit-v0.2.2/usage-kit/target/suite-groups/MOCK-SERVER-CROSS-VERIFY-v0.2/BATCH-MR6FWKVN/RUN-3892e93a-4521-48ec-8df2-5e834f7b5927/suite_summary.yaml`

Covered combinations:

- REST client + WireMock HTTP mock, pass and expected fail.
- SOAP mock + HTTP client, pass and expected fail.
- gRPC mock + gRPC client, pass and expected fail.

## Golden E2E And YAML Report

Golden E2E full run:

```yaml
run_status: passed
suite_id: GOLDEN-E2E-v0.2
batch_id: BATCH-GOLDEN-E2E-001
run_id: RUN-GOLDEN-E2E-001
test_count: 1
passed_count: 1
failed_count: 0
provider_runtime_executed: true
fake_provider_executed: true
evidence_classification: framework_verification_only
```

YAML report:

```yaml
report_status: review_ready
coverage_percent: 100.0
release_evidence_eligible: false
missing_evidence_count: 0
masking_status: passed
findings: []
```

Evidence:

- `usage-kit-v0.2.2/usage-kit/target/provider-capability/golden-e2e/GOLDEN-E2E-v0.2/BATCH-GOLDEN-E2E-001/RUN-GOLDEN-E2E-001/result.json`

## Evidence Hardening

| Sample | Expected | Observed |
|---|---|---|
| `samples/evidence_hardening/valid_result.json` | pass | `evidence_validation_status: passed` |
| `samples/evidence_hardening/invalid_missing_evidence_result.json` | fail | `EVIDENCE_MISSING_EVIDENCE_INDEX` |
| `samples/evidence_hardening/invalid_secret_leak_result.json` | fail | `SECRET_GUARDRAIL_RAW_SECRET` |

## Profile Validation Consistency

Wrong profile tested:

```sh
--suite samples/provider_capability/mock_server_cross_verify/suite_manifest.yaml --profile local_mock_cross
```

Observed:

| Entry point | Exit | Status | Failure code |
|---|---:|---|---|
| `validate` | 1 | `validation_status: failed` | `CONFIGURATION_PROFILE_MISMATCH` |
| `run --dry-run` | 1 | `run_status: blocked` | `CONFIGURATION_PROFILE_MISMATCH` |
| `run` | 1 | `run_status: blocked` | `CONFIGURATION_PROFILE_MISMATCH` |

This closes the v0.2.1 dry-run/full-run profile mismatch gap.

## Security Findings

`release-assets-v0.2.2/dependency-check-report.json` was queried for dependencies with non-null `vulnerabilities`.

Observed result: no vulnerability rows returned.

Conclusion: no untriaged dependency vulnerabilities were found in the bundled dependency-check JSON during this PI-run.

## Resource Check

Representative timed command:

```sh
/usr/bin/time -l java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar validate \
  --suite samples/golden_e2e/suite_manifest.yaml \
  --profile local_golden
```

Observed:

- maximum resident set size: `105185280` bytes
- peak memory footprint: `82789240` bytes

This is below the requested 8G safety limit.

## Final Acceptance Decision

Do not mark v0.2.2 as fully accepted for complete custom-application PI-run yet.

Accept v0.2.2 for:

- suite-mode execution hardening,
- provider capability evaluation,
- mock server cross verification,
- evidence validation,
- golden E2E reporting,
- RP-mode deprecation,
- profile validation consistency.

Block full custom-application PI-run acceptance until:

- custom native REST result generation and report validation agree on `release_evidence_eligible`;
- the same custom REST run produces `report_status: review_ready`;
- the regression is covered in the release verification commands or usage kit.
