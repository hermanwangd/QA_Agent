# PI-run v0.2.1 Feature Coverage Matrix

Date: 2026-07-04 Asia/Taipei

Scope: GitHub release assets for `Auto_Regression_Test_Framework` v0.2.1 only. No source checkout was used.

Legend:

- PASS: executed successfully with release jar.
- PARTIAL: some paths pass, but an important advertised or expected path does not.
- BLOCKED: framework rejected the path before useful execution.
- WARN: not a functional failure, but a release-readiness risk.
- LEGACY: executed, but not counted as current PI-run acceptance evidence because the path is obsolete.
- NOT COVERED: sample or concept observed, but no executable acceptance path was completed in this PI-run.

## Executive Matrix

| Area | Coverage | Evidence | Result | Notes |
|---|---:|---|---|---|
| Release asset integrity | 4/4 assets | SHA-256 for jar, usage-kit zip, BOM JSON, BOM XML matched `release-assets-v0.2.1/checksums.sha256` | PASS | Asset-only workflow; no source clone. |
| Version identity | jar manifest | `Implementation-Version: 0.2.1` | PASS | Confirms tested jar version. |
| CLI command shape | observed commands | `run`, `validate`, `report`, `validate-evidence` | PASS | There is no literal `pi-run` command; PI-run maps to the `run` command. |
| Golden E2E | validate, dry-run, full run, report, evidence | `GOLDEN-E2E-v0.2`, `RUN-GOLDEN-E2E-001` | PASS | `sample_fake_provider`; 1 test, 2 verifies. |
| Evidence hardening | valid + invalid examples | `validate-evidence --result samples/evidence_hardening/...` | PASS | Valid result passed; missing evidence and raw secret samples failed as expected. |
| Mock server cross verification | REST/WireMock, SOAP, gRPC; pass and expected-fail cases | `MOCK-SERVER-CROSS-VERIFY-v0.2`, `BATCH-MR6ASZ5C`, `RUN-3a7941fb-486c-49f8-a0e6-8b62c36f8d37` | PASS | 6/6 passed, including 3 expected-failure cases. |
| Provider P0 parent suite | 11 child suites via group runner | `PROVIDER-CAPABILITY-P0-v0.2`, `BATCH-MR6AUBCB`, `RUN-2ab30cea-c14b-4e85-9823-ff43c8f5f357` | PARTIAL | Parent group failed 3/11 passed, 8 rejected as `VALIDATION_UNSUPPORTED_PROVIDER_TYPE`. |
| Provider individual suites | WireMock, JDBC, NATS, common verify, polling, Kafka, IBM MQ, mixed messaging | individual `run --suite ...` commands | PASS | Individual runtime paths pass even when parent group rejects them. |
| Current custom app PI-run via suite-mode | validate, dry-run, full run | `pi_run_demo/dummy_rest/suite_manifest.yaml` | BLOCKED | validate/dry-run pass; full run blocked because executable suite mode supports framework-owned `sample_fake_provider` only. |
| RP-mode native REST app | dry-run, full run, report | `RP-DUMMY-REST-001`, `BATCH-002`, `RUN-003` | LEGACY | Executed successfully, but excluded from current PI-run acceptance because RP-mode is obsolete and should be removed. |
| RP coverage report | batch report artifacts | `evidence/review/BATCH-002/coverage_report.yaml` | LEGACY | `coverage_percent: 100.0`, `review_ready: true`, but not counted for current framework acceptance. |
| Security scan | dependency-check report | `release-assets-v0.2.1/dependency-check-report.json` | WARN | 7 MEDIUM findings in bundled dependencies. |
| Resource constraint | representative timed run | max RSS `104235008` bytes under `-Xmx512m` | PASS | Well below the 8G machine safety limit. |

## Provider And Verifier Detail

| Capability | Tested path | Result | Evidence / observed ID | Finding |
|---|---|---|---|---|
| `sample_fake_provider` | Golden E2E full run | PASS | `RUN-GOLDEN-E2E-001` | Baseline framework smoke path works. |
| `wiremock_http_mock` | individual `wiremock` suite | PASS | `RUN-WIREMOCK-20260704114850428-1` | Runtime executed WireMock. |
| `wiremock_http_mock` + `rest_client` | `wiremock_http_request` child and cross-verify REST | PASS | `BATCH-MR6ASZ5C` REST-001/REST-002 | Both passing and expected-failing REST paths covered. |
| `soap_mock` + `rest_client` | provider child and cross-verify SOAP | PASS | `BATCH-MR6ASZ5C` SOAP-001/SOAP-002 | Both passing and expected-failing SOAP paths covered. |
| `grpc_mock` + `grpc_client` | provider child and cross-verify gRPC | PASS | `BATCH-MR6ASZ5C` GRPC-001/GRPC-002 | Both passing and expected-failing gRPC paths covered. |
| `jdbc` | individual JDBC suite | PASS | `RUN-JDBC-20260704114914240-1` | Ephemeral Oracle-like runtime path executed. |
| `nats` | individual NATS suite | PASS | `RUN-NATS-20260704114921135-1` | Mock NATS event-bus path executed. |
| `kafka` | individual Kafka suite | PASS | `RUN-KAFKA-20260704114926105-1` | Mock Kafka topic path executed. |
| `ibm_mq` | individual IBM MQ suite | PASS | `RUN-IBMMQ-20260704114931511-1` | Mock MQ queue path executed. |
| Kafka + IBM MQ mixed messaging | individual mixed suite | PASS | `RUN-MESSAGING-20260704114943740-1` | 2-test mixed messaging path executed. |
| `common_verify` | individual common verify suite | PASS | `RUN-COMMON-1783165702706` | `json_match`, `schema_match`, and `file_diff` passed. |
| polling via `common_verify` | individual polling suite | PASS | `RUN-COMMON-1783165718956` | Polling capability path passed. |
| `request_response/rest` in RP mode | custom dummy app RP package | LEGACY | `RUN-003` | Native HTTP POST `/orders` executed, but RP-mode should be removed and is not current acceptance evidence. |
| Provider P0 group runner | parent group suite | PARTIAL | `BATCH-MR6AUBCB` | Group dispatch rejects 8 child suites as unsupported even though individual suites pass. |
| Custom suite-mode `rest_client` | repo-local `pi_run_demo/dummy_rest` | BLOCKED | `CONTRACT_UNSUPPORTED_SUITE_RUNTIME` | Full suite-mode runtime is limited to framework-owned `sample_fake_provider`. |
| `artifact_compare` sample folder | `samples/provider_capability/compare` | NOT COVERED | no suite manifest in folder | Sample data exists, but no executable suite path was completed. |

## DSL Findings

Suite-mode DSL:

- The v0.2 sample style with `targets`, `data`, `execute.operations`, `verify.checks`, `cleanup`, `evidence`, and `runtime` validates and dry-runs.
- Full execution of arbitrary custom suite-mode REST is blocked in v0.2.1 by `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`.

Legacy RP-mode DSL observation:

- Native REST full execution works through release-package layout under `docs/08-release/release-packages/<rp_id>`, but this path is obsolete and should not be used as the target PI-run model.
- `generated-framework/run_plan.yaml`, `run_profiles/<env>.yaml`, `environment_bindings/<env>.yaml`, and `provider_contracts/*.yaml` are required runtime artifacts.
- REST provider contracts must use `provider_contract_kind: request_response` and `provider_type: rest`.
- Request bodies worked through `execute.operations[].with.<binding>.bind_as: api_payload` plus a generated binding contract.
- Simple output aliases such as `status`, `headers`, and `body` are safer than dotted aliases in RP assertions.
- `json_path_equals` worked in RP mode. `value_equals` and `json_match` are validated by suite samples, but RP assertion execution was reliable with `json_path_equals`.
- RP report requires an `acceptance_criteria.md` file that is YAML-readable with top-level `acceptance_criteria:`.

## Release Risks

| Risk | Severity | Evidence | Recommendation |
|---|---|---|---|
| Provider P0 parent suite fails despite individual child suites passing | High | `VALIDATION_UNSUPPORTED_PROVIDER_TYPE` for 8/11 children in `BATCH-MR6AUBCB` | Fix suite-group dispatch support or update provider parent expectations. |
| Current custom app PI-run is blocked in suite-mode | High | `CONTRACT_UNSUPPORTED_SUITE_RUNTIME` for `pi_run_demo/dummy_rest` | Extend suite-mode runtime dispatch to support custom provider contracts and remove reliance on RP-mode. |
| Obsolete RP-mode still exists in CLI/runtime | High | `run --root --rp-id --env` and `report --root --rp-id --batch-id` executed | Remove RP-mode or mark it deprecated until deleted; do not use it for current acceptance. |
| `validate --root --rp-id --env` is inconsistent | Low | observed `Missing required option: --suite` | Prefer deleting RP validation path with RP-mode removal. |
| Top-level jar with no command starts Spring and fails bean creation | Medium | observed no-argument invocation error | Add CLI help/default usage behavior. |
| `report --format yaml` is unsupported | Low | observed `Unsupported --format: yaml` | Document supported output formats or implement YAML flag. |
| Dependency-check reports 7 MEDIUM findings | Medium | `dependency-check-report.json` | Triage dependency upgrades or suppressions before production adoption. |
