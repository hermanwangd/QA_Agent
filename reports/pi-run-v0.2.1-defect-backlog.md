# PI-run v0.2.1 Defect Backlog

Date: 2026-07-04 Asia/Taipei

Source evidence:

- `reports/pi-run-v0.2.1-full-acceptance-report.md`
- `reports/feature_coverage_matrix.md`
- release assets under `release-assets-v0.2.1/`
- usage-kit execution evidence under `usage-kit-v0.2.1/usage-kit/target/`
- dummy app suite evidence under `pi_run_demo/dummy_rest/`

Current verdict: current PI-run is not complete. RP-mode is obsolete and should not count as current acceptance evidence. The target model should be suite-mode.

## Priority Summary

| Priority | Count | Theme |
|---|---:|---|
| P0 | 3 | Blocks current full PI-run |
| P1 | 7 | Blocks clean release certification or creates inconsistent operator experience |
| P2 | 4 | Release quality, docs, metadata, and coverage cleanup |

## P0 Blockers

### PI-P0-001: Suite-mode cannot full-run custom provider tests

Status: Open

Evidence:

```text
run_status: blocked
reason: unsupported_suite_runtime
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
owner_action: Executable suite mode supports framework-owned sample_fake_provider only.
```

Repro:

```sh
java -Xmx512m -jar release-assets-v0.2.1/spec-driven-auto-regression-0.2.1.jar run \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy
```

Impact:

- Prevents current PI-run from testing a real custom application through suite-mode.
- Forces users toward obsolete RP-mode or framework-owned samples.

Suggested fix:

- Extend suite-mode runtime dispatch to execute custom provider instances and provider contracts.
- At minimum support `rest_client` with fixture binding, HTTP execution, output capture, assertions, evidence index, and report.
- Use the same runtime registry used by the working individual provider samples.

Acceptance criteria:

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy
```

Expected:

```yaml
run_status: passed
provider_runtime_executed: true
provider_type: rest_client
test_count: 1
failed_count: 0
```

### PI-P0-002: Provider P0 parent suite rejects child suites that pass individually

Status: Open

Evidence:

- Parent suite: `PROVIDER-CAPABILITY-P0-v0.2`
- Latest observed batch: `BATCH-MR6AUBCB`
- Latest observed run: `RUN-2ab30cea-c14b-4e85-9823-ff43c8f5f357`
- Parent result: 3 passed, 8 failed.
- Failure code: `VALIDATION_UNSUPPORTED_PROVIDER_TYPE`.
- Individual suites for the rejected capabilities pass when executed directly.

Examples of individual pass evidence:

| Suite | Run ID |
|---|---|
| WireMock | `RUN-WIREMOCK-20260704114850428-1` |
| JDBC | `RUN-JDBC-20260704114914240-1` |
| NATS | `RUN-NATS-20260704114921135-1` |
| Common verify | `RUN-COMMON-1783165702706` |
| Polling | `RUN-COMMON-1783165718956` |
| Kafka | `RUN-KAFKA-20260704114926105-1` |
| IBM MQ | `RUN-IBMMQ-20260704114931511-1` |
| Mixed messaging | `RUN-MESSAGING-20260704114943740-1` |

Impact:

- Parent capability report is misleading.
- Release cannot claim provider P0 full green even though lower-level runtime support exists.

Suggested fix:

- Make suite-group execution call the same child-suite code path as direct `run --suite child/suite_manifest.yaml --profile child_profile`.
- Remove or unify separate provider-type whitelist logic in the suite-group runner.
- Parent suite should compare observed child status against `expected_status`, not pre-block supported provider types differently from direct execution.

Acceptance criteria:

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/suite_manifest.yaml \
  --profile local_provider
```

Expected:

```yaml
run_status: passed
test_count: 11
passed_count: 11
failed_count: 0
```

### PI-P0-003: Obsolete RP-mode still exists and can be mistaken for the current PI-run path

Status: Open

Evidence:

- `run --root . --rp-id RP-DUMMY-REST-001 --env local_dummy` executes.
- `report --root . --rp-id RP-DUMMY-REST-001 --batch-id BATCH-002` executes.
- RP-mode produced a passing dummy REST result, but it is obsolete and should not count as current acceptance.

Impact:

- Confuses framework users about the correct operating model.
- Encourages skills/docs to encode legacy behavior.
- Hides the suite-mode custom-provider blocker.

Suggested fix:

- Remove RP-mode commands and code paths, or hard-deprecate them with explicit warnings until deletion.
- Delete or isolate RP-only assumptions such as `docs/08-release/release-packages`, `acceptance_criteria.md`, and `generated-framework/*` from current PI-run docs.
- Move any useful provider-contract execution behavior into suite-mode.

Acceptance criteria:

- No current documentation recommends RP-mode.
- `run --root --rp-id --env` either does not exist or prints a deprecation/removal message.
- Suite-mode can execute the same dummy REST case without RP package layout.

## P1 Release Certification Issues

### PI-P1-004: Suite-mode report and coverage are not the clear canonical path

Status: Open

Evidence:

- `report --result <suite result.json>` works for golden E2E.
- Rich coverage/traceability report was only proven through obsolete RP-mode.

Impact:

- Current suite-mode PI-run lacks a clear end-to-end reporting contract for custom apps.

Suggested fix:

- Define suite-mode report output as canonical:
  - coverage summary
  - evidence index
  - assertion summary
  - provider evidence summary
  - traceability from suite/test metadata
- Avoid dependency on RP files.

Acceptance criteria:

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar report \
  --result target/dummy-rest/.../result.json
```

Expected:

```yaml
report_status: review_ready
coverage_percent: 100.0
missing_evidence_count: 0
masking_status: passed
```

### PI-P1-005: DSL validation and runtime support are inconsistent

Status: Open

Evidence:

- Suite-mode dummy REST validates and dry-runs but full execution is blocked.
- Some constructs validate in one mode but have different runtime behavior depending on execution path.

Impact:

- Users can write DSL that appears valid but cannot run.

Suggested fix:

- Add a runtime-capability validation phase to `validate`.
- `validate` should report whether each operation/assertion/provider is executable in the selected mode/profile.
- Keep assertion semantics consistent across suite-mode and provider samples.

Acceptance criteria:

- A valid suite should be executable unless explicitly marked dry-run-only or sample-only.
- Unsupported runtime features should fail at validation with a precise remediation.

### PI-P1-006: Profile handling differs between dry-run and full run

Status: Open

Evidence:

- `mock_server_cross_verify` dry-run accepted `--profile local_mock_cross`.
- Full run rejected it and required `local_mock_server_cross_verify`.

Impact:

- Operators can get false confidence from dry-run.

Suggested fix:

- Apply identical profile validation in validate, dry-run, and full run.
- Include allowed profile IDs in the error output.

Acceptance criteria:

- Wrong profile fails consistently at validate/dry-run/full-run.
- Correct profile passes consistently.

### PI-P1-007: CLI help and no-command behavior are broken

Status: Open

Evidence:

- `java -jar ... --help` returns `Unknown command: --help`.
- `java -jar ...` starts Spring and fails with bean creation / constructor error.

Impact:

- New users cannot discover correct command usage.
- No-command invocation looks like an application crash.

Suggested fix:

- Add top-level `help` / `--help` support.
- Add command-specific help.
- Print friendly usage when no command is provided.
- Do not initialize Spring application context for invalid/no CLI command paths.

Acceptance criteria:

```sh
java -jar spec-driven-auto-regression-0.2.2.jar --help
java -jar spec-driven-auto-regression-0.2.2.jar
java -jar spec-driven-auto-regression-0.2.2.jar run --help
```

Expected: exit code 0 for help, concise usage output, no stack trace.

### PI-P1-008: User-facing "pi-run" command is not available

Status: Open

Evidence:

- The actual command is `run`; there is no literal `pi-run`.

Impact:

- Naming mismatch between user workflow and CLI.

Suggested fix:

- Either add `pi-run` as an alias for `run`, or document that PI-run means the `run` command.
- Prefer alias if this framework is marketed around PI-run.

Acceptance criteria:

```sh
java -jar spec-driven-auto-regression-0.2.2.jar pi-run --suite ... --profile ...
```

Expected: same behavior as `run`.

### PI-P1-009: Report `--format yaml` flag is unsupported

Status: Open

Evidence:

- `report --format yaml` returned `Unsupported --format: yaml`.

Impact:

- Inconsistent automation expectations; YAML output is useful for CI parsing.

Suggested fix:

- Add documented output format support, or remove the flag from docs/help.

Acceptance criteria:

- `report --format yaml` emits YAML and exits 0, or help clearly lists only supported formats.

### PI-P1-010: Dependency-check reports MEDIUM CVEs

Status: Open

Evidence:

| Dependency | CVE | Severity | Score |
|---|---|---:|---:|
| `commons-lang3-3.17.0.jar` | `CVE-2025-48924` | MEDIUM | 5.3 |
| `jackson-databind-2.22.0.jar` | `CVE-2026-54515` | MEDIUM | 5.3 |
| `wiremock-grpc-extension-core-1.0.0-beta.5.jar` | `CVE-2023-41329` | MEDIUM | 6.6 |
| `wiremock-grpc-extension-core-1.0.0-beta.5.jar` | `CVE-2018-9117` | MEDIUM | 5.3 |
| `wiremock-grpc-extension-jetty-1.0.0-beta.5.jar` | `CVE-2023-41329` | MEDIUM | 6.6 |
| `wiremock-grpc-extension-jetty-1.0.0-beta.5.jar` | `CVE-2018-9117` | MEDIUM | 5.3 |
| `wiremock-httpclient-apache5-4.0.0-beta.38.jar` | `CVE-2020-13956` | MEDIUM | 5.3 |

Impact:

- Blocks clean production-readiness signoff unless triaged.

Suggested fix:

- Upgrade vulnerable dependencies where possible.
- If a CVE is false-positive or not exploitable in this framework, add a documented suppression with rationale.

Acceptance criteria:

- Dependency-check has no untriaged MEDIUM/HIGH/CRITICAL findings.

## P2 Quality And Coverage Issues

### PI-P2-011: BOM metadata contains generic or suspicious external references

Status: Open

Evidence:

- BOM metadata includes Spring Boot style external references for the framework component.

Impact:

- Release metadata quality issue; may confuse SBOM consumers.

Suggested fix:

- Set correct project website, VCS, issue tracker, license, author, and component identity.

Acceptance criteria:

- SBOM metadata points to the actual framework project and release.

### PI-P2-012: Artifact compare sample is present but not executable

Status: Open

Evidence:

- `samples/provider_capability/compare` contains provider contracts, test case, expected results, and actual samples.
- No executable suite manifest path was completed in this PI-run.

Impact:

- Feature appears present but cannot be counted as covered.

Suggested fix:

- Add a `suite_manifest.yaml` for artifact compare.
- Add it to the relevant provider capability parent suite if it is intended as a supported feature.

Acceptance criteria:

```sh
java -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/compare/suite_manifest.yaml \
  --profile local_compare
```

Expected: pass with `json_match`, `schema_match`, and `file_diff` evidence.

### PI-P2-013: Output paths and evidence conventions need tightening

Status: Open

Evidence:

- Different capability families write to different target subtrees.
- Parent suite, individual suite, and legacy RP reports use different evidence conventions.

Impact:

- Harder to automate report collection and skill authoring.

Suggested fix:

- Define a stable suite-mode output contract:
  - `target/<suite_id>/<batch_id>/<run_id>/result.json`
  - `evidence_index.yaml`
  - `assertions/`
  - `provider-evidence/`
  - `logs/`
  - `batch/`

Acceptance criteria:

- All suite-mode runtimes follow the same output structure or publish a machine-readable artifact index.

### PI-P2-014: Framework sample expectations need explicit status taxonomy

Status: Open

Evidence:

- Parent suites include `expected_status`.
- Some full suites intentionally include expected failures.
- Provider P0 parent reports rejected child suites as failed.

Impact:

- Reviewers can confuse "expected failure validated" with "framework failure".

Suggested fix:

- Standardize result statuses:
  - `passed`
  - `failed`
  - `blocked`
  - `expected_failed_observed`
  - `expected_failed_missing`
  - `unsupported`
- Make parent summaries count expected-failure validations separately.

Acceptance criteria:

- Parent summary clearly distinguishes framework failures from expected negative-test outcomes.

## Suggested v0.2.2 Acceptance Gates

Gate 1: current suite-mode app PI-run

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite pi_run_demo/dummy_rest/suite_manifest.yaml \
  --profile local_dummy
```

Gate 2: provider parent suite full green

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/suite_manifest.yaml \
  --profile local_provider
```

Gate 3: mock server cross verification

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite samples/provider_capability/mock_server_cross_verify/suite_manifest.yaml \
  --profile local_mock_server_cross_verify
```

Gate 4: canonical suite report

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar report \
  --result target/.../result.json
```

Gate 5: obsolete RP-mode removed or loudly deprecated

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run --root . --rp-id RP-DUMMY-REST-001 --env local_dummy
```

Expected: command unavailable or explicit deprecation/removal message; not a silent supported path.

## Recommended Fix Order

1. Remove or hard-deprecate RP-mode from the current workflow.
2. Implement suite-mode custom provider execution for REST.
3. Unify suite-group dispatch with individual child-suite dispatch.
4. Make suite-mode report the canonical report path.
5. Tighten CLI help, profile validation, output format behavior, and artifact conventions.
6. Add executable artifact-compare coverage.
7. Triage dependency-check findings and SBOM metadata.
