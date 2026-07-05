# Framework Fix Proposal for v0.2.2 PI-run Findings

Date: 2026-07-04 Asia/Taipei

Target owner: `Auto_Regression_Test_Framework`

Scope: framework changes only. This proposal intentionally excludes Testcontainers provisioning. Project-side PI-run owns provisioning and writes standard framework artifacts before invoking the jar.

## Goal

Make the framework execute and report correctly when it receives already-materialized standard artifacts:

- `suite_manifest.yaml`
- `test_case.yaml`
- `env_profiles/<profile>.yaml`
- `environment_bindings/<profile>.yaml`
- `execution_profiles/*`
- `provider_instances/*`
- fixtures/expected results

The framework must not require project-specific generated-ref consumption or `--binding-overrides`.

## Found Issues Addressed

### FW-P0-001: `contract_baseline` full run is blocked before provider runtime

Evidence:

```yaml
run_status: blocked
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_runtime_invoked: false
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
provider_type: jdbc,nats,wiremock_http_mock
```

Required framework fix:

- Route suite-mode tests using supported provider types into the existing provider runtimes.
- Do not block a suite only because it combines `jdbc`, `nats`, and `wiremock_http_mock`.
- If materialized bindings are missing or invalid, fail with configuration/binding errors after artifact loading.

Acceptance:

```yaml
run_status: passed
provider_runtime_invoked: true
provider_types_used:
  - jdbc
  - nats
  - wiremock_http_mock
```

### FW-P0-002: Unresolved generated refs should fail explicitly

Framework should not resolve project-specific generated refs. The PI-run project must remove or replace `generated://...` before calling the framework.

Required framework fix:

- Detect unresolved `generated://` refs in standard artifacts.
- Fail fast with a precise error.

Acceptance:

```yaml
run_status: blocked
failure_code: CONFIGURATION_UNRESOLVED_GENERATED_REF
owner_action: Materialize generated refs into standard env_profile/environment_binding artifacts before running the framework.
```

### FW-P0-003: Custom native REST report rejects valid execution evidence

Evidence:

```yaml
report_status: invalid
failure_code: VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM
field_path: provider_results.release_evidence_eligible
```

Required framework fix:

- Align result generation and report validation evidence policy.
- If suite labels say `downstream_release_evidence: false`, generated provider result must set `release_evidence_eligible: false`.
- Native `rest_client` should not be rejected as `mock_release_evidence_claim` when labels already mark it framework/local-only.

Acceptance:

```yaml
report_status: review_ready
release_evidence_eligible: false
missing_evidence_count: 0
masking_status: passed
findings: []
```

### FW-P1-004: Provider support matrix lacks executable clarity

Required framework/docs fix:

- Add columns to provider support matrix:
  - `executable_in_release`
  - `sample_path`
  - `release_evidence_eligible_modes`
  - `notes`

Acceptance:

Each documented provider type is explicitly one of:

- executable sample included;
- contract-only;
- escape-hatch;
- deprecated;
- future slice.

## Explicit Non-goals

- Do not embed Testcontainers into the framework jar.
- Do not add `--binding-overrides`.
- Do not add framework-side project generated-ref resolver.
- Do not start Docker containers from framework runtime.

## Required Tests

### Dispatcher regression

Input: materialized `contract_baseline` sample with no `generated://` refs.

Expected:

```yaml
provider_runtime_invoked: true
```

### Placeholder validation

Input: same sample but with `generated://oracle-ephemeral.connection`.

Expected:

```yaml
failure_code: CONFIGURATION_UNRESOLVED_GENERATED_REF
```

### Custom REST report regression

Input: dummy REST result where:

```yaml
downstream_release_evidence: false
```

Expected:

```yaml
report_status: review_ready
release_evidence_eligible: false
```

## Release Acceptance

Framework release can be accepted for this fix when:

```text
contract_baseline materialized full run: PASS
custom REST report: PASS
provider parent suite: PASS
mock cross verify: PASS
evidence hardening: PASS
```
