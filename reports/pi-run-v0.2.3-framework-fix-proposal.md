# Framework Fix Proposal for v0.2.3 PI-run Findings

Date: 2026-07-04 Asia/Taipei

Status: Proposed

Target owner: `Auto_Regression_Test_Framework`

Scope: framework changes only. This proposal intentionally excludes Testcontainers provisioning, RU startup orchestration, Docker lifecycle management, and project-specific artifact generation. The PI-run project owns provisioning and must pass already-materialized standard framework artifacts into the released jar.

## Goal

Make the framework execute and report correctly when it receives valid standard suite-mode artifacts:

- `suite_manifest.yaml`
- `test_case.yaml`
- `env_profiles/<profile>.yaml`
- `environment_bindings/<profile>.yaml`
- `execution_profiles/*`
- `provider_instances/*`
- fixtures and expected results

The framework must not require project-specific generated-ref resolution, `--binding-overrides`, or legacy RP-mode execution.

## Current v0.2.2 Baseline

Verified against the released v0.2.2 jar:

- Provider parent suite: PASS, 12/12.
- Mock cross-verify suite: PASS.
- Evidence hardening validate/report: PASS.
- Dummy native REST execution/report: PASS.
- `contract_baseline` full run: BLOCKED with `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`.

Therefore, v0.2.3 should focus on the remaining framework dispatch and validation gaps instead of reworking already-passing evidence/report behavior.

## P0 Fixes

### FW-P0-001: Mixed Provider Suite Dispatch

Evidence:

```yaml
run_status: blocked
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_runtime_invoked: false
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
provider_type: jdbc,nats,wiremock_http_mock
```

Problem:

The suite uses provider types that the framework supports individually, but the dispatcher blocks before runtime because the combination is not routed. A valid materialized suite should not fail only because it combines supported providers.

Required framework fix:

- Route suite-mode tests containing multiple supported provider types into executable runtime flow.
- Resolve each target through Provider Instance, Provider Contract, Env_Profile, and Environment Binding before dispatch.
- Dispatch only supported executable provider operations.
- Preserve deterministic setup, execute, verify, cleanup, evidence, and result JSON order.
- If a target is missing binding data or uses a non-executable provider mode, fail with configuration or contract findings after artifact validation, not with generic unsupported-suite-runtime.

Acceptance:

```yaml
run_status: passed
provider_runtime_invoked: true
provider_types_used:
  - jdbc
  - nats
  - wiremock_http_mock
findings: []
```

Required tests:

- `contract_baseline` materialized full run executes with `provider_runtime_invoked: true`.
- Mixed provider result JSON contains provider results for `jdbc`, `nats`, and `wiremock_http_mock`.
- Evidence index validates after the mixed run.
- Unsupported provider type inside the same suite still blocks with an owner-actionable `CONTRACT_UNSUPPORTED_PROVIDER_TYPE` style finding.

### FW-P0-002: Unresolved Generated Ref Validation

Boundary:

`generated_ref` is a valid public interface when it targets a Provider Contract `bindable_outputs` entry or a declared Env_Profile dependency provisioner output. The framework must not reject all `generated://...` refs.

Problem:

Unresolved or undeclared generated refs must fail before provider dispatch with a precise owner action. Silent pass-through makes PI-run failures hard to diagnose.

Required framework fix:

- Validate every `generated_ref` and generated `secret_ref` before dispatch.
- Accept refs produced by a selected provider's declared `bindable_outputs`.
- Accept refs produced by an approved dependency provisioner declared in the selected Env_Profile.
- Block refs with no declared producer, no selected provider, or no matching output key.
- Include artifact path, field path, provider_id, profile, and owner action.

Acceptance:

```yaml
run_status: blocked
failure_code: CONFIGURATION_UNRESOLVED_GENERATED_REF
category: CONFIGURATION_ERROR
owner_action: Declare the generated ref producer in Provider Contract bindable_outputs or Env_Profile dependency provisioner outputs, or materialize the value before running.
```

Required tests:

- Valid WireMock `generated://wiremock-payment-api.base_url` passes.
- Valid dependency-provisioner JDBC/NATS generated secrets pass when declared.
- Undeclared `generated://oracle-ephemeral.connection` blocks before provider runtime.
- Generated ref pointing to a provider not selected by the suite blocks before provider runtime.

### FW-P0-003: Release Evidence Policy Regression Guard

Current state:

Native REST report passed in v0.2.2. Do not change all REST results to `release_evidence_eligible: false`.

Required framework guard:

- If suite/provider labels set `downstream_release_evidence: false`, generated provider results must set `release_evidence_eligible: false`.
- If suite/provider labels set `downstream_release_evidence: true`, native executable provider evidence may remain `release_evidence_eligible: true`.
- Mock/local-only providers must not claim downstream release evidence.
- `regress report` must apply the same policy as result generation.

Acceptance for framework/local-only sample:

```yaml
report_status: review_ready
release_evidence_eligible: false
missing_evidence_count: 0
masking_status: passed
findings: []
```

Acceptance for native REST release-evidence candidate:

```yaml
report_status: review_ready
release_evidence_eligible: true
findings: []
```

Required tests:

- Framework/local-only REST sample reports `release_evidence_eligible: false`.
- Dummy native REST release-evidence candidate reports `release_evidence_eligible: true`.
- Mock provider result claiming release evidence is rejected with `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`.

## P1 Documentation Fix

### FW-P1-004: Provider Support Matrix Clarity

Add or update provider matrix columns:

- `executable_in_release`
- `sample_path`
- `release_evidence_eligible_modes`
- `status`
- `notes`

Each documented provider type must be classified as one of:

- executable sample included;
- contract-only;
- escape-hatch;
- deprecated;
- future slice.

This is useful for production readiness, but it should not block the P0 dispatch fix.

## Explicit Non-goals

- Do not embed Testcontainers into the framework jar.
- Do not add `--binding-overrides`.
- Do not add a project-specific generated-ref resolver.
- Do not restart or deploy RUs from provider runtime.
- Do not re-enable public legacy RP-mode.
- Do not weaken evidence or secret guardrails.

## Release Acceptance for v0.2.3

Framework release can be accepted when:

```text
contract_baseline materialized full run: PASS
generated_ref valid producer cases: PASS
generated_ref unresolved cases: PASS
custom REST report policy guard: PASS
provider parent suite: PASS
mock cross verify: PASS
evidence hardening validate/report: PASS
full Maven verify: PASS
security scan: PASS
```

## Recommended Implementation Order

1. Add failing tests for mixed provider dispatch and unresolved generated refs.
2. Implement generic suite target resolution and dispatch path for supported mixed-provider suites.
3. Add generated-ref producer validation before provider runtime dispatch.
4. Add release evidence policy regression tests without changing valid native REST semantics.
5. Update provider support matrix documentation.
6. Run full local verification, CI, then cut `v0.2.3`.
