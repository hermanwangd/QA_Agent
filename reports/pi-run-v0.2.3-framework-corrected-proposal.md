# pi-run Framework Corrected Proposal (v0.2.3 Baseline through v0.2.5 Evidence)

Created: 2026-07-05 Asia/Taipei

Last updated: 2026-07-09 Asia/Taipei

Status: Rolling framework proposal after review

Owner: `Auto_Regression_Test_Framework`

Scope: Framework-owned changes only. This proposal tracks framework release issues found from v0.2.3 release-asset PI-run evidence plus later v0.2.5 project-side evidence. It does not ask the framework jar to provision Docker/Testcontainers dependencies or own project-side pi-run orchestration.

Separation rule: this file tracks only changes that belong in the `Auto_Regression_Test_Framework` release. Project/pi-run harness changes belong in `reports/pi-run-v0.2.3-project-corrected-proposal.md`.

Filename note: the file path keeps the original v0.2.3 name for continuity with existing proposal references. The content is now a rolling framework proposal through the v0.2.5 evidence set.

## Evidence Baselines

Baseline A: v0.2.3 release assets only:

- `release-assets-v0.2.3/spec-driven-auto-regression-0.2.3.jar`
- `usage-kit-v0.2.3/usage-kit`
- `release-assets-v0.2.3/checksums.sha256`
- `reports/pi-run-v0.2.3-report.md`

Observed v0.2.3 state:

| Area | Status | Note |
|---|---:|---|
| Mixed `wiremock_http_mock` + `jdbc` + `nats` suite | PASS | Removes the v0.2.2 mixed-suite blocker. |
| Framework-managed WireMock mock runtime | PASS | Framework-owned WireMock capability runtime executes. |
| Project-provisioned external WireMock `base_url` consumption | NOT_PROVEN | Project Docker WireMock starts, but framework runtime did not prove it consumed that external URL. |
| `report` / `validate-evidence` release verification commands | GAP | Usage-kit release commands do not cover them. |
| Public `pi-run` CLI surface | GAP | The framework should not expose project acceptance orchestration as a public command. |
| Public RP-mode | GAP | Direct public RP-mode is obsolete and must be removed or blocked. |
| Release detached signature verification | PASS with integrity limitation | Raw detached signatures verify with release-provided certificate public keys; certificate chain trust and provenance verification were not performed. |

Current v0.2.3 project-side pi-run coverage result:

| Status | Count | Meaning |
|---|---:|---|
| `PASS` | 14 | Runnable release usage-kit cases were executed through suite-mode. |
| `BLOCKED_USAGE_KIT_SAMPLE_GAP` | 14 | Framework claims or registry entries exist, but the release usage-kit has no executable sample for the claimed public provider capability. |
| `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | 4 | Framework marks Kafka and IBM MQ as contract-only instead of executable supported runtimes. |
| `BLOCKED_DEPRECATED_ALIAS` | 3 | Deprecated aliases should not be used by new artifacts. |
| `BLOCKED_SAFETY_POLICY` | 0 | Safety-policy blocking is not part of the corrected framework/project contract. |

Conclusion: all 35 pi-run provider capability observations were accounted for; all executable release-asset-backed observations were tested; non-executable observations are framework-owned contract/sample/deprecation issues, not project-side safety-policy blocks.

Baseline B: added v0.2.5 release-asset and project-side evidence:

- `reports/pi-run-v0.2.5-goal-audit.md`
- `reports/pi-run-v0.2.5-testcontainers-heavy-jdbc-report.md`

Observed v0.2.5 additions:

| Area | Status | Note |
|---|---:|---|
| Runnable release usage-kit matrix | PASS | 36 suites and 108 commands executed with 0 unexpected failures; support-status split still needs release-gate consistency checks. |
| Project-provisioned WireMock external `base_url` consumption | NOT_PROVEN_WITH_FRAMEWORK_ISSUE | Framework run passes, but external `base_url` is still not proven consumed by the provider runtime. |
| Project-provisioned Oracle/DB2 JDBC external `env://` connection consumption | NOT_PROVEN_WITH_FRAMEWORK_ISSUE | Oracle and DB2 Testcontainers reach framework invocation, but JDBC runtime fails with `SECRET_RESOLUTION_ERROR` for `env://JDBC_CONNECTION`. |
| Raw secret scan | PASS | 766 files scanned, 0 findings. |

## Framework Issue Backlog

These are framework-owned issues found by release-asset PI-run evidence. They must be tracked in the framework proposal, not hidden as project harness work.

Target release convention: `post-v0.2.5 next release` means the next framework release after v0.2.5. If the actual tag is not v0.2.6, the release candidate still must satisfy the same gates before claiming the issue fixed.

| Issue | Observed in | Target release | Current pi-run status | Framework action |
|---|---|---|---:|---|
| Public `pi-run` CLI surface | v0.2.3 | post-v0.2.5 next release | `GAP` | Remove from framework help/docs/usage-kit workflows, or block as non-public project orchestration. |
| Direct public RP-mode | v0.2.3 | post-v0.2.5 next release | `GAP` | Remove as an obsolete public runtime path, or hide as compatibility-only behavior with a structured deprecated/blocking result. |
| Missing or incomplete `report` / `validate-evidence` release verification commands | v0.2.3; partially improved in v0.2.5 | post-v0.2.5 next release | `PARTIAL_RELEASE_GATE` | Keep already-added report/evidence checks and promote positive plus negative fixtures to mandatory release verification. |
| `report --format json` public contract ambiguity | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT` | Keep JSON outside the public report contract unless explicitly reintroduced with passing release verification; unsupported JSON must exit `2`. |
| Project-provisioned WireMock external `base_url` | v0.2.3, v0.2.5 | post-v0.2.5 next release | `NOT_PROVEN_WITH_FRAMEWORK_ISSUE` | Support external binding values such as `base_url`, prove the runtime consumed that URL, and fail validation only for missing, malformed, or secret-bearing values. |
| Project-provisioned JDBC external `env://` connection secret ref | v0.2.5 | post-v0.2.5 next release | `NOT_PROVEN_WITH_FRAMEWORK_ISSUE` | Resolve project-supplied JDBC connection secret refs such as `env://JDBC_CONNECTION`, consume the resolved external connection in JDBC runtime, and redact the connection/password in all evidence. |
| Provider support matrix drift control | v0.2.3, v0.2.5 | post-v0.2.5 next release | `GAP` | Generate and enforce registry/contracts/support-matrix/sample consistency during release verification. |
| `grpc_client` sample gap | v0.2.3 | already improved in v0.2.5; keep regression gate | `PASS_IN_V0.2.5` | Keep executable release usage-kit samples and enforce support matrix consistency so the gap does not regress. |
| `rest_client` sample gap | v0.2.3 | already improved in v0.2.5; keep regression gate | `PASS_IN_V0.2.5` | Keep executable release usage-kit samples and enforce support matrix consistency so the gap does not regress. |
| `polling_observer` sample gap | v0.2.3 | already improved in v0.2.5; keep regression gate | `PASS_IN_V0.2.5` | Keep executable release usage-kit samples and enforce support matrix consistency so the gap does not regress. |
| `shell_command` support truthfulness | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | Add executable release usage-kit samples if supported; otherwise keep explicit `contract_only`/`unsupported` status and block before dispatch. |
| `external_runner` support truthfulness | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | Add executable release usage-kit samples if supported; otherwise keep explicit `contract_only`/`unsupported` status and block before dispatch. |
| `kubernetes_runtime` support truthfulness | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | Add executable release usage-kit samples if supported; otherwise keep explicit `contract_only`/`unsupported` status and block before dispatch. |
| `vm_runtime` support truthfulness | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | Add executable release usage-kit samples if supported; otherwise keep explicit `contract_only`/`unsupported` status and block before dispatch. |
| Kafka / IBM MQ remaining runtime coverage claims | v0.2.3, v0.2.5 | post-v0.2.5 next release | `PARTIAL_PASS_WITH_CONTRACT_ONLY_ROWS` | Keep working executable samples passing; either complete remaining claimed runtime/profile coverage rows or remove/downgrade unsupported claims. |
| `kafka_messaging/*` deprecated alias | v0.2.3, v0.2.5 | post-v0.2.5 next release | `BLOCKED_DEPRECATED_ALIAS` | Remove from public registry/docs/samples or keep hidden compatibility-only behavior that cannot be used by new artifacts. |
| Safety-policy blocking in public provider accounting | v0.2.3 | post-v0.2.5 next release | `CONTRACT_CORRECTION` | Keep `BLOCKED_SAFETY_POLICY` absent; unsupported command-capable provider claims must be sample gaps, explicit blocks, or downgraded/removed claims. |
| Evidence/report raw secret publication guardrail | v0.2.3, v0.2.5 | post-v0.2.5 next release | `REQUIRED_FRAMEWORK_GUARDRAIL` | `validate-evidence` and `report` must fail or redact before publishing raw secrets from provider evidence. |
| Release provenance and certificate chain trust | v0.2.3, v0.2.5 | post-v0.2.5 next release | `INTEGRITY_LIMITATION` | Raw detached signatures pass; release notes should document signing trust/provenance verification or explicitly mark the limitation. |

## Next Release Scope Decision

The next framework release after v0.2.5 is not a small documentation patch. It is a framework release truthfulness and runtime completion release with four boundaries:

- public provider support is represented by one field: `support_status`;
- `native`, `ephemeral`, `framework_managed`, and `external` are not public provider support modes;
- Kafka and IBM MQ provider types cannot be marked `supported` unless they have runtime implementation and executable suite-mode samples; unverified runtime/profile coverage must be documented separately and must not become a public support status;
- `report --format json` is not part of the public report contract unless it is explicitly reintroduced with passing release verification.

Public provider support statuses:

| `support_status` | Meaning |
|---|---|
| `supported` | Public contract exists, runtime implementation exists, at least one CI-verifiable executable usage-kit sample exists, and release verification passes. |
| `contract_only` | Public contract exists, but runtime execution is not available; validation must block before dispatch. |
| `deprecated` | Compatibility-only provider or alias; new artifacts and samples must not use it. |
| `unsupported` | Not part of the public provider capability surface. |

Release rule:

```text
If a provider cannot satisfy the full `supported` definition, it must not be published as supported.
No provider support claim may pass by documentation claim alone.
```

## Framework Boundary

The framework should expose only suite-mode runtime behavior:

- `validate`
- `run`
- `run --dry-run`
- `report`
- `validate-evidence`

The framework must not own:

- project-side `pi-run` command semantics;
- Docker/Testcontainers provisioning;
- release asset download orchestration;
- project-specific matrix generation;
- Product/RP/RU topology inference.

## FW-P0-001: Remove Public `pi-run` and Public RP-mode

Observed in: `v0.2.3`.

Target release: post-v0.2.5 next framework release.

Problem:

v0.2.3 exposes `pi-run` in CLI help, and compatibility docs still mention direct Product/RP runner behavior. That conflicts with the intended boundary: pi-run is project acceptance orchestration, not a framework command.

Required change:

- Remove `pi-run` from public help, public docs, usage-kit verification commands, and recommended workflows.
- Keep only canonical suite-mode commands: `validate`, `run`, `run --dry-run`, `report`, `validate-evidence`.
- Direct public RP-mode must not be a release gate.
- If legacy RP-mode remains temporarily, make it compatibility-only:
  - hidden from help;
  - documented as deprecated/blocked;
  - exits `2` for unsupported public command usage, or exits `1` with a structured `LEGACY_RP_MODE_DEPRECATED` blocked result;
  - tells users to generate suite-mode artifacts and call `run --suite`.

Acceptance:

```text
java -Xmx512m -jar spec-driven-auto-regression-<candidate>.jar --help
# lists validate, run, report, validate-evidence
# does not list pi-run or direct RP-mode as public runtime

java -Xmx512m -jar spec-driven-auto-regression-<candidate>.jar pi-run --help
# exits 2, or exits 1 with LEGACY_RP_MODE_DEPRECATED if kept as compatibility blocker
```

## FW-P0-002: Support Project-provisioned WireMock External `base_url`

Observed in: `v0.2.3`, `v0.2.5`.

Target release: post-v0.2.5 next framework release.

Problem:

Framework-managed WireMock works, but project-provisioned external WireMock `base_url` consumption was not proven in v0.2.3 or v0.2.5. The target release must support this path instead of silently falling back to a framework-managed mock.

Required change:

- Document and test two supported cases:
  - framework-managed `wiremock_http_mock`: supported, executable, framework-verification-only;
  - project-provisioned external WireMock `base_url`: supported through Env_Profile or Environment Binding consumption.
- Resolve `generated://<provider_id>.base_url`, static Env_Profile values, or predefined generated binding values into the WireMock/HTTP client provider runtime and prove the external endpoint was used.
- When external `base_url` is supplied, the framework must not start a framework-managed WireMock instance for that provider.
- Missing, malformed, or secret-bearing `base_url` must fail validation before provider dispatch with an owner-actionable error.

Acceptance:

```yaml
project_provisioned_wiremock:
  expected_status: passed
  framework_consumed_project_dependency: true
  consumed_binding_keys: [base_url]
  framework_started_wiremock: false
  external_base_url_consumed: true
```

## FW-P0-003: Generate and Enforce Provider Support Matrix

Observed in: `v0.2.3`; partially improved in `v0.2.5`.

Target release: post-v0.2.5 next framework release, with regression gates for gaps already closed in v0.2.5.

Problem:

Manual provider coverage claims drift across registry, contracts, docs, and samples.

v0.2.3 PI-run found release usage-kit sample gaps. v0.2.5 closed several of those gaps, but the target release must enforce the public provider `support_status` level so gaps do not regress:

- `grpc_client`
- `rest_client`
- `polling_observer`
- `shell_command`
- `external_runner`
- `kubernetes_runtime`
- `vm_runtime`

Required change:

- Replace the legacy split support accounting model with a single public `support_status` field:
  - `supported`
  - `contract_only`
  - `deprecated`
  - `unsupported`
- Add a release check comparing:
  - `docs/02-architecture/contracts/provider_capability_registry.v0.2.yaml`
  - `docs/02-architecture/contracts/provider-contracts/*.yaml`
  - `docs/09-operations/provider_support_matrix.md`
  - `samples/provider_capability/**`
  - `samples/contract_baseline/**`
- Fail release verification when:
  - a registry provider has no provider contract;
  - a provider contract has no registry entry unless explicitly service/internal/deprecated;
  - support matrix status conflicts with provider contract, implementation, or sample evidence;
  - a `contract_only` provider is dispatched into runtime execution;
  - a `deprecated` provider or alias is used by new samples;
  - a `supported` provider has no CI-verifiable executable release usage-kit sample;
  - a `supported` provider sample cannot pass validate, run, report, and validate-evidence verification.

Provider semantics to preserve:

| Provider | Target status | Release policy |
|---|---|---|
| `kafka` | `supported` at provider-type level when the supported definition is met | Runtime implementation and executable usage-kit samples are required for each runtime/profile coverage row claimed by docs or samples. |
| `ibm_mq` | `supported` at provider-type level when the supported definition is met | Runtime implementation and executable usage-kit samples are required for each runtime/profile coverage row claimed by docs or samples. |
| `kafka_messaging` | `deprecated` | Compatibility only; new artifacts must use `kafka`. |
| `shell_command` | `supported` or `contract_only` | Must have executable samples if supported; otherwise block before dispatch. |
| `external_runner` | `supported` or `contract_only` | Must have executable samples if supported; otherwise block before dispatch. |
| `kubernetes_runtime` | `supported` or `contract_only` | Must have executable samples if supported; otherwise block before dispatch. |
| `vm_runtime` | `supported` or `contract_only` | Must have executable samples if supported; otherwise block before dispatch. |

Acceptance:

```text
registry_without_contract = []
support_matrix_conflicts = []
contract_only_runtime_dispatch = []
deprecated_alias_used_by_new_samples = []
supported_provider_claims_without_usage_kit_sample = []
supported_provider_claims_with_failed_release_verification = []
```

## FW-P0-004: Remove Safety Policy Blocking From Public Provider Support Claims

Observed in: `v0.2.3`.

Target release: post-v0.2.5 next framework release.

Problem:

v0.2.3 project-side pi-run originally treated command-capable providers without release usage-kit samples as safety-policy blocked. That is the wrong public contract: the framework should not require a project safety policy merely to account for a public provider support claim.

The correct framework-owned issue is coverage truthfulness. If `shell_command`, `external_runner`, `kubernetes_runtime`, or `vm_runtime` are claimed as supported, the release must provide executable samples or explicitly downgrade/remove the unsupported provider claims.

Required change:

- Remove `BLOCKED_SAFETY_POLICY` from the provider support matrix and release acceptance vocabulary.
- Do not require `safety.access_policy` as a framework-level prerequisite for public provider support accounting.
- For command-capable provider claims with no executable release sample, report `BLOCKED_USAGE_KIT_SAMPLE_GAP` or downgrade/remove the unsupported claim.
- Redact command arguments, environment variables, stdout, stderr, logs, and collected files according to evidence guardrails.
- Fail report publication if raw secrets appear in evidence or report output.

Acceptance:

```text
BLOCKED_SAFETY_POLICY = absent from release provider matrix
command_capable_rows_without_samples = BLOCKED_USAGE_KIT_SAMPLE_GAP or downgraded/removed
raw_secret_in_provider_evidence = validate-evidence/report fail
```

## FW-P0-005: Complete `report` and `validate-evidence` Release Coverage

Observed in: `v0.2.3`; partially improved in `v0.2.5`.

Target release: post-v0.2.5 next framework release.

Problem:

`usage-kit-v0.2.3/release/verification_commands.md` covers `validate` and `run`, but not `report` or `validate-evidence`. Later framework verification added some report/evidence checks, but the next release should treat them as first-class release gates with both positive and negative fixtures.

Project-side pi-run also proved that v0.2.3 returns exit `2` for `report --format json` with unsupported format.

Required change:

- Add release verification commands for:
  - `validate-evidence --result <valid_result_json>`
  - `report --result <valid_result_json> --format text`
  - `report --result <valid_result_json> --format yaml`
- Keep `report --format json` outside the public contract unless explicitly reintroduced with passing release verification.
- Add an unsupported-format negative check:
  - `report --result <valid_result_json> --format json` exits `2`
  - stdout/stderr clearly says JSON report format is unsupported in this release
- Add negative fixtures and expected exits:
  - missing evidence file;
  - malformed result JSON;
  - schema-invalid result JSON;
  - inconsistent `test_count` vs `test_results`;
  - raw secret in provider evidence;
  - blocked provider result;
  - failed assertion result.

Acceptance:

| Command | Valid expected | Invalid expected |
|---|---:|---:|
| `validate-evidence` | exit `0` | exit `1` |
| `report --format text` | exit `0`, review-ready summary | exit `1` |
| `report --format yaml` | exit `0`, parseable YAML | exit `1` |
| `report --format json` | not public unless explicitly reintroduced | exit `2`, unsupported format |

## FW-P0-006: Release Asset Integrity Beyond Checksums

Observed in: `v0.2.3`, `v0.2.5`.

Target release: post-v0.2.5 next framework release.

Problem:

v0.2.3 checksum verification passed, and raw detached signatures verify with release-provided certificate public keys. Certificate chain trust and release provenance verification were not performed.

Required change:

- Publish detached signatures, public verification instructions, certificate trust expectations, and build provenance, or explicitly document which integrity checks are not available.
- Release notes should include jar checksum, usage-kit checksum, signing method, certificate/provenance trust status, and build provenance if available.

Acceptance:

```yaml
checksum_verification: passed
raw_signature_verification: passed
certificate_chain_trust: not_proven
build_provenance: not_proven
release_decision: accepted_with_integrity_limitation
```

## FW-P0-007: Complete or Downgrade Kafka and IBM MQ Runtime Coverage Claims

Observed in: `v0.2.3`; partially improved in `v0.2.5` with remaining contract-only runtime/profile coverage rows.

Target release: post-v0.2.5 next framework release.

Problem:

v0.2.3 accounts for Kafka and IBM MQ provider observations as `BLOCKED_FRAMEWORK_CONTRACT_ONLY`. v0.2.5 adds executable Kafka and IBM MQ suite-mode samples for some paths, but still reports remaining contract-only runtime/profile coverage rows such as `kafka/ephemeral` and `ibm_mq/ephemeral`.

The framework proposal target is truthfulness and executable support: every Kafka or IBM MQ runtime/profile coverage claim must either execute through suite-mode with project-provided connection materialization when needed, or be downgraded/removed from the documented release coverage.

This is a target-release gate, not a stretch item. Provider type `support_status` remains provider-level. If a runtime/profile coverage row cannot pass executable release verification, the target release must not present that row as supported release coverage.

`native` and `ephemeral` are server-side or environment descriptors, not public provider support statuses and not substitutes for evidence. Provider type support and runtime/profile release coverage must be reported separately:

```yaml
kafka:
  support_status: supported
  verified_runtime_coverage: [native]
  unverified_runtime_coverage: [ephemeral]
ibm_mq:
  support_status: supported
  verified_runtime_coverage: [native]
  unverified_runtime_coverage: [ephemeral]
```

Required change:

- Keep verified Kafka runtime execution paths working.
- Keep verified IBM MQ runtime execution paths working.
- Implement any remaining claimed Kafka/IBM MQ runtime/profile coverage rows, or remove/downgrade them from release coverage with validation blocking before dispatch when they are attempted.
- Accept project-provided connection/binding material such as host, port, credentials, queue/topic/channel/manager names, and generated connection URLs without the framework owning Docker/Testcontainers provisioning.
- Add executable release usage-kit suite-mode samples for every Kafka/IBM MQ runtime/profile coverage row claimed as release-verified.
- Keep v0.2.3-style contract-only blocking only as the pre-implementation behavior, not as the target outcome.
- If a runtime/profile coverage row cannot pass executable release verification, that row must not be published as verified release coverage.

Minimum Kafka runtime slice:

- publish message;
- observe/consume message;
- payload match;
- timeout/polling;
- masked evidence;
- owner-actionable connection, timeout, and assertion failures.

Minimum IBM MQ runtime slice:

- put message;
- get/observe message;
- payload match;
- timeout/polling;
- masked evidence;
- owner-actionable connection, timeout, and assertion failures.

Acceptance:

```yaml
kafka:
  support_status: supported
  verified_runtime_coverage:
    native:
      release_usage_kit_sample: pass
      validate: pass
      run: pass
      report: pass
      validate_evidence: pass
  unverified_runtime_coverage_not_presented_as_supported: true
  unsupported_or_contract_only_runtime_coverage_blocks_before_dispatch: true
ibm_mq:
  support_status: supported
  verified_runtime_coverage:
    native:
      release_usage_kit_sample: pass
      validate: pass
      run: pass
      report: pass
      validate_evidence: pass
  unverified_runtime_coverage_not_presented_as_supported: true
  unsupported_or_contract_only_runtime_coverage_blocks_before_dispatch: true

framework_owns_provisioning: false
framework_consumes_project_bindings: true
contract_only_runtime_coverage_claims_are_explicit: true
```

## FW-P0-008: Support Project-provisioned JDBC `env://` Connection Secret Refs

Observed in: `v0.2.5`.

Target release: post-v0.2.5 next framework release.

Problem:

v0.2.5 Oracle and DB2 Testcontainers PI-run attempts proved that project-side heavy JDBC provisioning can reach framework invocation, but the framework JDBC provider runtime exits with `SECRET_RESOLUTION_ERROR`:

```text
failure_reason: JDBC secret_ref `env://JDBC_CONNECTION` cannot be resolved by local provider capability runtime.
```

Evidence:

- Oracle: `.pirun/runs/PIRUN-TC-ORACLE-1783593641329/jdbc_oracle_testcontainers/framework_stdout.txt`
- DB2: `.pirun/runs/PIRUN-TC-DB2-1783595732804/jdbc_db2_testcontainers/framework_stdout.txt`
- Report: `reports/pi-run-v0.2.5-testcontainers-heavy-jdbc-report.md`

Required change:

- Add one framework secret resolver path used by provider runtimes for all contract-declared `secret_ref` binding keys.
- Resolve JDBC `connection.secret_ref` values from project-supplied environment references such as `env://JDBC_CONNECTION`.
- Pass the resolved external JDBC connection material into the JDBC provider runtime.
- Keep Docker/Testcontainers provisioning outside the framework jar.
- Preserve project-owned driver provisioning through classpath or documented runtime extension points.
- Redact the resolved connection string, username/password fragments, and provider evidence before stdout/stderr/report publication.
- Return owner-actionable validation errors when an `env://` secret ref is missing, blank, or unsupported.

Secret resolver contract:

- The resolver applies only to provider binding keys that the provider contract explicitly allows to use `secret_ref`.
- Supported target scheme for this issue: `env://<ENV_NAME>`.
- `env://` names must match environment variable name syntax: `A-Z`, `0-9`, and `_`, starting with a letter or `_`.
- Missing environment variables fail before provider dispatch with `SECRET_RESOLUTION_ERROR`.
- Blank environment variables fail before provider dispatch with `SECRET_RESOLUTION_ERROR`.
- Unsupported schemes fail validation or pre-dispatch resolution with `UNSUPPORTED_SECRET_REF_SCHEME`.
- Resolved secret values must never appear in stdout, stderr, provider evidence, report output, or validation errors.
- Existing `generated://` provider capability refs must continue to work.

JDBC binding contract:

The minimum supported shape for the target release is the full connection secret ref already used by the v0.2.5 heavy JDBC harness:

```yaml
binding_values:
  connection:
    secret_ref: env://JDBC_CONNECTION
```

The target release may pass `FW-P0-008` with the full connection ref only. Split JDBC URL/user/credential refs are future contract work unless the provider contract explicitly declares those fields and adds matching release verification.

Acceptance:

```yaml
oracle_heavy_jdbc:
  framework_owns_provisioning: false
  framework_consumes_project_connection_ref: true
  secret_ref: env://JDBC_CONNECTION
  provider_runtime_executed: true
  provider_id: oracle-like-db
  run_status: passed

db2_heavy_jdbc:
  framework_owns_provisioning: false
  framework_consumes_project_connection_ref: true
  secret_ref: env://JDBC_CONNECTION
  provider_runtime_executed: true
  provider_id: db2-like-db
  run_status: passed

raw_connection_secret_in_evidence: false
missing_env_secret_ref: owner_actionable_failure
```

Executable release verification:

```text
validate external_jdbc_env_secret_ref suite: exit 0
run --dry-run external_jdbc_env_secret_ref suite: exit 0
run external_jdbc_env_secret_ref suite with project-provided JDBC_CONNECTION: exit 0
report --result <external_jdbc_result_json> --format text: exit 0, no raw connection value
report --result <external_jdbc_result_json> --format yaml: exit 0, no raw connection value
validate-evidence --result <external_jdbc_result_json>: exit 0
```

Negative release verification:

```text
validate malformed env secret ref URI: exit 1, owner-actionable validation error
run missing JDBC_CONNECTION: exit 1, SECRET_RESOLUTION_ERROR
run blank JDBC_CONNECTION: exit 1, SECRET_RESOLUTION_ERROR
run unsupported secret ref scheme: exit 1 or validate exit 1, UNSUPPORTED_SECRET_REF_SCHEME
report result containing raw JDBC credential material: exit 1 or redacted output before publication
validate-evidence result containing raw JDBC credential material: exit 1
```

## Framework Deliverables

- Updated CLI help and compatibility behavior.
- Updated `framework_usage_interface.v0.2.md`.
- Provider support matrix generated from registry/contracts/samples using `support_status`.
- Added `report` and `validate-evidence` release verification commands.
- Removed JSON report format from the public contract unless explicitly reintroduced with passing release verification, while keeping unsupported-format behavior owner-actionable.
- Added release usage-kit samples or explicit `contract_only`/`deprecated`/`unsupported` declarations for currently uncovered provider runtime/profile coverage claims.
- Completed or downgraded Kafka and IBM MQ runtime/profile coverage claims, with executable suite-mode samples for every coverage row published as release-verified.
- Added contract-declared `env://` secret-ref resolution for project-provisioned external database runtimes.
- Removed framework-level safety policy blocking from public provider support claims.
- Added command-capable provider sample coverage checks.
- Clear release integrity metadata.

## Framework Acceptance Gate

```text
framework public pi-run command: removed or blocked
public RP-mode: removed or blocked
provider support matrix uses support_status only
framework-managed WireMock capability: PASS
project-provisioned WireMock external base_url: PASS, consumed by runtime
provider support matrix consistency: PASS
command-capable providers without release samples: BLOCKED_USAGE_KIT_SAMPLE_GAP or downgraded/removed
report positive cases: PASS
report negative cases: EXPECTED_FAIL
report --format json: exit 2 unsupported format unless explicitly reintroduced with passing release verification
validate-evidence positive cases: PASS
validate-evidence negative cases: EXPECTED_FAIL
Kafka/IBM MQ provider support: provider-level support_status stays separate from runtime/profile coverage
Kafka/IBM MQ runtime/profile coverage claims: release-verified only after executable suite-mode verification, otherwise removed/downgraded/blocked
project-provisioned JDBC env:// connection ref: PASS, consumed by runtime
project-provisioned JDBC env:// negative cases: EXPECTED_FAIL with owner-actionable errors
usage-kit sample gaps: none for supported provider claims, or explicitly blocked/downgraded
release asset checksum metadata: present
release asset raw signature metadata: present
certificate chain/provenance limitation: explicitly documented
```
