# PI-run v0.2.1 Full Acceptance Report

Date: 2026-07-04 Asia/Taipei

Test subject: `Auto_Regression_Test_Framework` release v0.2.1, tested from release assets only:

- `release-assets-v0.2.1/spec-driven-auto-regression-0.2.1.jar`
- `release-assets-v0.2.1/spec-driven-auto-regression-0.2.1-usage-kit.zip`
- `release-assets-v0.2.1/bom.json`
- `release-assets-v0.2.1/bom.xml`
- `release-assets-v0.2.1/dependency-check-report.json`

## Verdict

Current PI-run: NOT COMPLETE.

The v0.2.1 release jar is usable for:

- Golden E2E sample execution and reporting.
- Evidence validation and secret/missing-evidence guardrails.
- Individual provider capability suites, including WireMock, JDBC, NATS, common verifier, polling, Kafka, IBM MQ, and mixed messaging.
- Mock server cross verification for REST/WireMock, SOAP, and gRPC, including expected-failure cases.

The release should not be accepted as complete current PI-run because:

- The provider P0 parent suite fails even though the individual child suites pass.
- Custom suite-mode full execution is blocked for non-framework-owned REST providers.
- RP-mode is obsolete and should be removed, so its successful dummy REST run is not counted as current acceptance evidence.
- A few CLI/documentation gaps remain around RP validation, help behavior, and report format flags.
- Dependency-check reports 7 MEDIUM vulnerability findings.

## Acceptance Evidence

### Release Asset Integrity

SHA-256 values were recalculated locally and matched `checksums.sha256`:

| Asset | SHA-256 |
|---|---|
| `spec-driven-auto-regression-0.2.1.jar` | `4d450555feebdf7bd5d0d633394a69f495aadc26b00299feea9640d710b3918c` |
| `spec-driven-auto-regression-0.2.1-usage-kit.zip` | `129a811fece541d4a5c823b35bbef4732d7e739dc316954203349576af7a704b` |
| `bom.json` | `3c4d86d621ae6240b588043ac5034f99c37eaed2ddbeb33726f20c05b1886f55` |
| `bom.xml` | `aef2fc9c36aec8c87149688f725cdfda9a68ddaf4cf8e56630b2d0b78ddac7c5` |

Jar manifest confirmed `Implementation-Version: 0.2.1`.

### Golden E2E

Commands exercised:

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.1.jar validate --suite samples/golden_e2e/suite_manifest.yaml
java -Xmx512m -jar spec-driven-auto-regression-0.2.1.jar run --suite samples/golden_e2e/suite_manifest.yaml --profile local_golden --dry-run
java -Xmx512m -jar spec-driven-auto-regression-0.2.1.jar run --suite samples/golden_e2e/suite_manifest.yaml --profile local_golden
java -Xmx512m -jar spec-driven-auto-regression-0.2.1.jar report --result target/golden-e2e/GOLDEN-E2E-v0.2/BATCH-GOLDEN-E2E-001/RUN-GOLDEN-E2E-001/result.json
```

Result:

- `suite_id: GOLDEN-E2E-v0.2`
- `run_id: RUN-GOLDEN-E2E-001`
- `status: passed`
- `verify_results_count: 2`
- `report_status: review_ready`
- `missing_evidence_count: 0`
- `masking_status: passed`

### Evidence Hardening

`validate-evidence` behaved correctly on positive and negative samples:

| Sample | Expected | Observed |
|---|---|---|
| `valid_result.json` | pass | `evidence_validation_status: passed` |
| `invalid_missing_evidence_result.json` | fail | `EVIDENCE_MISSING_EVIDENCE_INDEX` |
| `invalid_secret_leak_result.json` | fail | `SECRET_GUARDRAIL_RAW_SECRET` |

### Provider Capabilities

The provider P0 parent suite still fails:

- `suite_id: PROVIDER-CAPABILITY-P0-v0.2`
- `batch_id: BATCH-MR6AUBCB`
- `run_id: RUN-2ab30cea-c14b-4e85-9823-ff43c8f5f357`
- `passed_count: 3`
- `failed_count: 8`
- failure code: `VALIDATION_UNSUPPORTED_PROVIDER_TYPE`

However, individual suites passed:

| Suite | Run ID | Result |
|---|---|---|
| WireMock | `RUN-WIREMOCK-20260704114850428-1` | PASS |
| JDBC | `RUN-JDBC-20260704114914240-1` | PASS |
| NATS | `RUN-NATS-20260704114921135-1` | PASS |
| Common verify | `RUN-COMMON-1783165702706` | PASS |
| Polling | `RUN-COMMON-1783165718956` | PASS |
| Kafka | `RUN-KAFKA-20260704114926105-1` | PASS |
| IBM MQ | `RUN-IBMMQ-20260704114931511-1` | PASS |
| Mixed messaging | `RUN-MESSAGING-20260704114943740-1` | PASS |

Mock server cross verification also passed:

- `suite_id: MOCK-SERVER-CROSS-VERIFY-v0.2`
- `batch_id: BATCH-MR6ASZ5C`
- `run_id: RUN-3a7941fb-486c-49f8-a0e6-8b62c36f8d37`
- `test_count: 6`
- `passed_count: 6`
- `expected_failure_count: 3`

This covers REST/WireMock, SOAP mock, and gRPC mock positive and negative cases.

### Dummy Application Acceptance

A deterministic local REST service was added under `dummy_app/`:

- `GET /health`
- `POST /orders`
- `GET /orders/{id}`

Unit tests in `tests/test_dummy_app.py` cover health, order creation, order lookup, and invalid order rejection.

### Custom Suite-Mode DSL

`pi_run_demo/dummy_rest/suite_manifest.yaml` validates and dry-runs. Full suite-mode execution is blocked:

```yaml
run_status: blocked
reason: unsupported_suite_runtime
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
owner_action: Executable suite mode supports framework-owned sample_fake_provider only.
```

Conclusion: v0.2.1 suite-mode DSL is useful for validation/dry-run learning, but arbitrary custom REST provider execution should not be claimed through suite mode.

### Legacy RP-Mode Native REST Observation

The release-package style dummy REST acceptance case passed, but this is legacy evidence only. RP-mode is obsolete and should be removed from the framework, so this result is not counted toward current PI-run completion.

- RP package: `docs/08-release/release-packages/RP-DUMMY-REST-001`
- Batch: `BATCH-002`
- Run: `RUN-003`
- Test case: `DUMMY-REST-TC-001`
- AC: `RP-DUMMY-REST-001-AC-001`
- Status: `passed`
- Provider runtime: `request_response/rest`
- Assertion engine: `json_path_equals`

Evidence:

- `docs/08-release/release-packages/RP-DUMMY-REST-001/evidence/batches/BATCH-002/batch.yaml`
- `docs/08-release/release-packages/RP-DUMMY-REST-001/evidence/runs/RUN-003/run.yaml`
- `docs/08-release/release-packages/RP-DUMMY-REST-001/evidence/runs/RUN-003/assertions.yaml`
- `docs/08-release/release-packages/RP-DUMMY-REST-001/evidence/review/BATCH-002/coverage_report.yaml`
- `docs/08-release/release-packages/RP-DUMMY-REST-001/evidence/review/BATCH-002/traceability_report.yaml`

Report result:

```yaml
report_status: review_ready
coverage_percent: 100.0
covered: 1
total_automatable: 1
```

## How To PI-run This Framework

For v0.2.1, use this sequence:

1. Verify release assets and jar version.
2. Run golden E2E as the smoke test.
3. Run evidence hardening positive and negative samples.
4. Run mock server cross verification.
5. Run provider capability suites individually, not only the P0 parent group.
6. For a real application, use suite-mode as the target model, but treat v0.2.1 as blocked until suite-mode can execute custom provider contracts.
7. Do not use RP-mode as the current PI-run path; remove or deprecate it.

The current gap for real application PI-run is:

- suite-mode DSL can validate and dry-run a custom REST case.
- suite-mode full run rejects that case with `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`.
- the framework should move the working provider-contract execution concepts into suite-mode and delete the obsolete RP-mode surface.

## Security Findings

Dependency-check reported 7 MEDIUM findings:

| Dependency | CVE | Severity | Score |
|---|---|---:|---:|
| `commons-lang3-3.17.0.jar` | `CVE-2025-48924` | MEDIUM | 5.3 |
| `jackson-databind-2.22.0.jar` | `CVE-2026-54515` | MEDIUM | 5.3 |
| `wiremock-grpc-extension-core-1.0.0-beta.5.jar` | `CVE-2023-41329` | MEDIUM | 6.6 |
| `wiremock-grpc-extension-core-1.0.0-beta.5.jar` | `CVE-2018-9117` | MEDIUM | 5.3 |
| `wiremock-grpc-extension-jetty-1.0.0-beta.5.jar` | `CVE-2023-41329` | MEDIUM | 6.6 |
| `wiremock-grpc-extension-jetty-1.0.0-beta.5.jar` | `CVE-2018-9117` | MEDIUM | 5.3 |
| `wiremock-httpclient-apache5-4.0.0-beta.38.jar` | `CVE-2020-13956` | MEDIUM | 5.3 |

## Resource Check

All Java commands were run with `-Xmx512m`. A representative timed validate run reported:

- max RSS: `104235008` bytes
- peak memory footprint: `81822560` bytes

This is below the requested 8G safety limit.

## Final Acceptance Decision

Do not accept v0.2.1 as a complete current PI-run framework.

Accept it only for sample/provider capability evaluation and for learning the current DSL boundaries, with these required follow-ups before full acceptance:

- Use individual provider suites for provider capability verification.
- Treat provider P0 parent suite failure as a release defect or known limitation.
- Remove RP-mode or mark it deprecated until deletion.
- Implement custom provider full execution in suite-mode.
- Do not advertise arbitrary custom suite-mode REST execution as supported until it passes.
- Triage dependency-check MEDIUM findings before production adoption.
