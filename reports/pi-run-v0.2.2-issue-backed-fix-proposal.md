# PI-run v0.2.2 Issue-backed Fix Proposal

Date: 2026-07-04 Asia/Taipei

Scope: fixes proposed from v0.2.2 release-asset PI-run evidence.

Primary evidence:

- `reports/pi-run-v0.2.2-exhaustive-report.md`
- `reports/pi-run-v0.2.2-exhaustive-matrix.md`
- `reports/pi-run-v0.2.2-exhaustive-matrix.json`
- `reports/pi-run-v0.2.2-acceptance-report.md`

## Summary

The architectural direction remains:

- PI-run project owns dependency provisioning.
- PI-run project materializes dependency bindings into standard framework artifacts before execution.
- Framework jar owns suite dispatch, standard artifact loading, provider execution, evidence validation, and reporting.

But implementation must be driven by the found issues below. The first fix should not be Testcontainers code. The first fix should unblock framework suite dispatch so project-materialized artifacts can actually reach provider runtime.

## Found Issues

### PI-V022-P0-001: Contract baseline full run is blocked before provider runtime

Severity: P0

Evidence:

```yaml
run_status: blocked
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_runtime_invoked: false
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
provider_type: jdbc,nats,wiremock_http_mock
```

Impact:

- Project-side Testcontainers cannot help yet.
- Even with Docker running and project-provisioned values available, the framework blocks before provider runtime.
- `samples/contract_baseline/suite_manifest.yaml` can validate and dry-run, but cannot serve as executable PI-run evidence.

Root cause hypothesis:

- Suite runtime dispatch still rejects the provider set used by `contract_baseline`.
- The dispatcher does not route this suite into the existing `jdbc`, `nats`, and `wiremock_http_mock` execution paths.

Required fix:

- Update suite-mode dispatcher to route supported provider combinations instead of blocking the whole suite group.
- If bindings are unresolved, fail later with a binding error, not with unsupported suite runtime.

Acceptance:

```yaml
run_status: passed
provider_runtime_invoked: true
provider_types_used:
  - jdbc
  - nats
  - wiremock_http_mock
```

### PI-V022-P0-002: Project-side materialized artifact contract is missing

Severity: P0

Evidence:

- `contract_baseline` execution profiles declare Testcontainers-style generated refs.
- There is no proven PI-run project convention that materializes those generated refs into the standard `env_profiles` and `environment_bindings` files before invoking the framework.

Impact:

- PI-run project cannot safely provide externally provisioned endpoint/secret values without asking the framework to understand project-specific generated refs.
- Generated refs such as `generated://oracle-ephemeral.connection` remain placeholders inside framework input artifacts.

Required fix:

Do not add framework `--binding-overrides`.

The PI-run project must create a materialized run workspace that contains normal framework artifacts with generated refs already filled or replaced by secret refs.

Example project-owned output:

```text
.pirun/runs/<run_id>/contract_baseline/
  suite_manifest.yaml
  test_case.yaml
  env_profiles/ci.yaml
  environment_bindings/ci.yaml
  execution_profiles/ci_pr.yaml
  provider_instances/
  provider_contracts/
  fixtures/
  secrets/
    oracle-connection.txt
    nats-connection.txt
  provisioning_evidence.yaml
```

Example materialized `environment_bindings/ci.yaml`:

```yaml
environment_id: ci-contract-sample-materialized
profile: ci
provider_bindings:
  - provider_id: wiremock-payment-api
    runtime_mode: mock
    binding_values:
      mappings_ref: fixtures/wiremock/payment-api/
  - provider_id: oracle-database
    runtime_mode: ephemeral
    binding_values:
      connection:
        secret_ref: secrets/oracle-connection.txt
      dialect: oracle
  - provider_id: nats-event-bus
    runtime_mode: ephemeral
    binding_values:
      connection:
        secret_ref: secrets/nats-connection.txt
      subject: payments.accepted
      timeout: PT30S
      poll_interval: PT0.5S
```

Acceptance:

- Framework CLI remains unchanged:

```sh
java -Xmx512m -jar spec-driven-auto-regression-0.2.2.jar run \
  --suite .pirun/runs/<run_id>/contract_baseline/suite_manifest.yaml \
  --profile ci
```

- No `generated://` refs remain in the materialized run workspace.
- If project materialization is incomplete, framework fails with `CONFIGURATION_UNRESOLVED_GENERATED_REF` when reading the standard artifacts.
- Raw secret in result/evidence fails with existing secret guardrails.

### PI-V022-P0-003: Custom native REST report rejects valid execution evidence

Severity: P0

Evidence:

```yaml
report_status: invalid
failure_code: VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM
field_path: provider_results.release_evidence_eligible
```

Observed result mismatch:

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
      "release_evidence_eligible": true
    }
  ]
}
```

Impact:

- Custom REST suite can run.
- Evidence validation passes.
- Report cannot become `review_ready`, so the PI-run is not end-to-end complete.

Required fix:

- Result generation and report validation must use the same evidence eligibility policy.
- If `downstream_release_evidence: false`, generated provider result must not set `release_evidence_eligible: true`.

Acceptance:

```yaml
report_status: review_ready
release_evidence_eligible: false
missing_evidence_count: 0
masking_status: passed
findings: []
```

### PI-V022-P1-004: Testcontainers docs exist, but executable provisioning integration is not proven

Severity: P1

Evidence:

- Docker Desktop exists and can run after startup.
- `docker version` reports `client=28.4.0 server=28.4.0`.
- `contract_baseline` still blocks with `CONTRACT_UNSUPPORTED_SUITE_RUNTIME` after Docker is ready.
- The v0.2.2 jar does not include Testcontainers/docker-java runtime dependencies.

Impact:

- Users may believe `allowed_provisioners: [testcontainers]` means the framework will provision dependencies.
- In v0.2.2, Testcontainers must be project-side, or a future framework slice must explicitly add provisioning support.

Required fix:

- Clarify docs:
  - framework-managed provider execution is separate from project-side dependency provisioning;
  - `allowed_provisioners: [testcontainers]` does not imply the jar bundles Testcontainers.
- Add project-side provisioning/materialization contract and sample.

Acceptance:

- Usage kit includes a runnable example where PI-run project starts NATS/DB, fills standard framework artifacts, and framework runs those materialized artifacts without a binding override flag.
- If not supported, validation should warn or fail with a precise message before run.

### PI-V022-P1-005: Some documented provider types have no executable release-asset sample

Severity: P1

Evidence:

Documented but not represented by executable sample provider instances:

- `artifact_compare`
- `external_runner`
- `kafka_messaging`
- `kubernetes_runtime`
- `polling_observer`
- `shell_command`
- `vm_runtime`

Impact:

- Release-asset exhaustive matrix cannot certify these provider types.
- Current docs can be misread as executable coverage.

Required fix:

- For each documented provider type, explicitly label one of:
  - executable sample included;
  - contract-only;
  - escape-hatch requiring approval;
  - deprecated;
  - future slice.

Acceptance:

- Provider support matrix includes `sample_path` and `executable_in_release: true|false`.

### PI-V022-P1-006: Evidence classification taxonomy needs one more state for project-side ephemeral runs

Severity: P1

Evidence:

- Current report distinguishes framework verification and release evidence, but project-side Testcontainers runs are neither downstream release evidence nor pure mock-only framework samples.

Impact:

- Risk of overstating local/CI ephemeral evidence as product release evidence.

Required fix:

Add:

```yaml
evidence_classification: local_ci_ephemeral_only
downstream_release_evidence: false
release_evidence_eligible: false
```

Acceptance:

- Reports show project-side Testcontainers evidence as reviewable but not release-eligible.

## Revised Implementation Order

### Phase 1: Framework dispatcher and unresolved-placeholder validation

Files in framework repo likely affected:

- suite runtime dispatcher
- validation taxonomy
- standard environment/profile artifact loader
- report policy tests

Deliverables:

- No new binding override CLI.
- Standard artifact loading remains the only framework input path.
- `CONFIGURATION_UNRESOLVED_GENERATED_REF`.
- `contract_baseline` no longer fails with `CONTRACT_UNSUPPORTED_SUITE_RUNTIME` when given materialized standard artifacts.
- `contract_baseline` reaches provider runtime instead of dispatcher block.

### Phase 2: Project-side provisioner and materializer POC

Files in PI-run project:

```text
pirun/
  provisioners/
    start.py
    stop.py
  materialize/
    contract_baseline.py
  generated/
    provisioning_evidence.yaml
  secrets/
    .gitkeep
  runs/
    .gitkeep
```

Start with NATS only. Do not start Oracle/DB and WireMock until standard artifact materialization is proven.

Acceptance:

```yaml
provider_runtime_invoked: true
provider_type: nats
evidence_classification: local_ci_ephemeral_only
release_evidence_eligible: false
```

### Phase 3: Contract baseline E2E

Add DB and WireMock provisioning after NATS passes.

Acceptance:

```yaml
run_status: passed
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_types_used:
  - jdbc
  - nats
  - wiremock_http_mock
```

### Phase 4: Reporting and evidence hardening

Deliverables:

- provisioning evidence included in report;
- no raw secrets;
- cleanup evidence recorded;
- custom REST report blocker fixed.

## Decision

Proceed with project-side materialization, not framework-side generated-ref consumption. Project-side Testcontainers provisioning is the right ownership model, but it is blocked by framework dispatcher support and by the lack of a documented materialized-run-workspace convention in v0.2.2.
