---
name: auto-regression-test-framework
description: Use when working with the Auto Regression Test Framework or spec-driven-auto-regression artifacts for DSL test cases, suite-mode artifacts, provider or mock configuration, suite execution, usage-kit inspection, or framework acceptance reporting.
---

# Auto Regression Test Framework

## Overview

Use the Auto Regression Test Framework as a developer-facing suite-mode test framework. Support both normal developer work, such as creating DSL test cases and running suites, and framework acceptance work, such as release-asset verification and provider coverage PI-runs.

Default local workspace, when present:

```bash
cd /Users/herman_mbp2023/Documents/test_framework_pirun
```

If this local workspace is absent, locate the project-owned usage kit and release jar first. If neither is available, ask for the framework version and artifact location before authoring or running tests.

Respect the local resource constraint: keep Java/Maven/container runs bounded and avoid memory-heavy containers on this 8G machine unless the user explicitly asks.

## First Checks

1. Identify the requested framework version. If the user asks for latest/current release, verify it online before assuming it exists.
2. Use release assets and usage-kit files. Do not clone or use framework source unless the user explicitly asks.
3. Read the local workspace entry points before acting:
   - `README.md`
   - `pirun/framework_paths.py`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/09-operations/test_framework_user_guide.md`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/09-operations/provider_support_matrix.md`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/02-architecture/contracts/test_case_dsl.v0.2.schema.yaml`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/02-architecture/contracts/suite_manifest.v0.2.schema.yaml`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/02-architecture/contracts/provider_instance.v0.2.schema.yaml`
   - `artifacts/usage-kits/usage-kit-v<version>/usage-kit/docs/02-architecture/contracts/env_profile.v0.2.schema.yaml`
4. Treat suite-mode as the public runtime interface. RP/product commands are compatibility or wrapper concerns, not the default framework runtime path.

If a `regress` wrapper is unavailable, invoke the release jar directly:

```bash
java -Xmx512m -jar artifacts/release-assets/release-assets-v<version>/spec-driven-auto-regression-<version>.jar <command> ...
```

## Resolve Paths

Before running commands, resolve the version and paths explicitly:

```bash
VERSION="${VERSION:-0.2.5}"
JAR="artifacts/release-assets/release-assets-v${VERSION}/spec-driven-auto-regression-${VERSION}.jar"
USAGE_KIT="artifacts/usage-kits/usage-kit-v${VERSION}/usage-kit"
SUITE="${SUITE:-path/to/suite_manifest.yaml}"
PROFILE="${PROFILE:-ci}"

test -f "$JAR"
test -d "$USAGE_KIT"
test -f "$SUITE"
```

After `run`, capture the generated result path from stdout before invoking report commands:

```bash
java -Xmx512m -jar "$JAR" run --suite "$SUITE" --profile "$PROFILE" | tee run.out
RESULT_JSON="$(awk -F': ' '/^(result_json|suite_summary_json):/ {print $2}' run.out | tail -1)"
test -n "$RESULT_JSON"
test -f "$RESULT_JSON"
java -Xmx512m -jar "$JAR" report --result "$RESULT_JSON"
java -Xmx512m -jar "$JAR" validate-evidence --result "$RESULT_JSON"
```

## Developer Workflow

For creating or changing tests, work from the usage-kit sample closest to the target provider and behavior. Do not invent DSL shape from memory.

1. Choose a sample:
   - General golden path: `samples/00-getting-started/golden_e2e/`
   - Mixed contract baseline: `samples/10-contract-baseline/mixed_wiremock_jdbc_nats/`
   - Provider capability samples: `samples/20-provider-capability-p0/`
   - Cross-provider mock verification: `samples/30-cross-provider-groups/mock_server_cross_verify/`
2. Create or update suite artifacts in the project under test, not inside the usage-kit cache, unless the task is framework acceptance.
3. Author the minimum file set:
   - `suite_manifest.yaml`
   - `test_case.yaml`
   - `provider_instances/`
   - `env_profiles/`
   - compatibility inputs only when required: `environment_bindings/`, `execution_profiles/`
   - fixtures, expected results, SQL, mock mappings, and evidence requirements
4. Validate authored artifacts against the usage-kit schemas and the framework `validate` command before running providers.
5. Validate before running providers:

```bash
java -Xmx512m -jar "$JAR" validate --suite "$SUITE" --profile "$PROFILE"
java -Xmx512m -jar "$JAR" run --suite "$SUITE" --profile "$PROFILE" --dry-run
```

6. Provision project-owned dependencies only after validation passes. Then run and report:

```bash
java -Xmx512m -jar "$JAR" run --suite "$SUITE" --profile "$PROFILE"
java -Xmx512m -jar "$JAR" report --result "$RESULT_JSON"
java -Xmx512m -jar "$JAR" validate-evidence --result "$RESULT_JSON"
```

## DSL Authoring Rules

Use this mental model:

```text
DSL target -> provider_id -> Provider Instance -> provider_type
  -> built-in Provider Contract catalog -> selected Env_Profile
  -> Env_Profile.providers.<provider_id>.binding_keys
```

Write `test_case.yaml` with these sections when needed:

- Identity: `dsl_version`, `test_case_id`, `title`, `status`, `revision`.
- Traceability: `source_refs` and `labels`. Keep `source_refs` metadata-only.
- Profiles and targets: `compatible_profiles`, `targets`, and provider IDs.
- Data: checked-in fixture refs, expected-result refs, SQL refs, payload refs.
- `setup`: seed DB, load mock stubs, prepare fixtures.
- `execute`: provider operations such as HTTP request, DB query, event publish.
- `verify`: assertion/oracle checks, expected values, polling options.
- `cleanup`: reset mock state, cleanup DB data, release project fixtures.
- `evidence`: required evidence files and assertion evidence.
- `runtime`: timeout and retry policy.

Keep runtime artifacts out of `source_refs`. Put executable material in `data`, operation `inputs`, fixtures, expected refs, or provider/env profile bindings.

## Minimal Suite Skeleton

Prefer copying the nearest usage-kit sample, then adapt IDs, provider IDs, fixtures, and expected refs. Use this minimal shape only as a starting point:

```yaml
# suite_manifest.yaml
contract_version: v0.2
suite_id: PROJECT-SMOKE-regression
selection:
  mode: suite
  suite: project-smoke
tests:
  - test_case.yaml
profiles:
  - ci
```

```yaml
# test_case.yaml
dsl_version: v0.2
test_case_id: PROJECT-SMOKE-TC-001
title: Verify one project behavior
status: active
revision: 1
source_refs:
  acceptance_criteria: docs/acceptance_criteria.md#AC-001
labels:
  tags: [smoke]
compatible_profiles: [ci]
targets:
  service_under_test:
    provider_id: service-under-test
data:
  request_payload:
    ref: fixtures/request.json
execute:
  operations:
    - id: call_service
      target: service_under_test
      operation: http_request
      inputs:
        request.method:
          value: POST
        request.path:
          value: /example
        request.body:
          ref: ${data.request_payload}
      outputs:
        status: status
verify:
  checks:
    - id: status_is_200
      type: value_equals
      actual:
        ref: ${execute.call_service.outputs.status}
      expected: 200
evidence:
  required:
    - assertions/status_is_200.yaml
runtime:
  timeout: PT1M
  retry:
    max_attempts: 1
```

Before running, replace placeholder provider IDs and operation/type names with values confirmed in the provider contract and sample for the chosen provider type.

## Provider Guidance

Use canonical provider types from the usage-kit provider support matrix.

| Provider area | Preferred approach |
|---|---|
| WireMock / HTTP mock | Use `wiremock_http_mock` samples. If using an externally provisioned WireMock, keep project-owned `base_url` materialization separate from framework-owned provider contracts. |
| REST client | Use `rest_client` with explicit owner/project endpoint bindings and checked-in expected request/response fixtures. |
| JDBC | Start with lightweight H2 or owner-provided disposable DB bindings. Preserve nested `connection.secret_ref`; do not flatten binding keys. Avoid Oracle XE-like containers on this 8G machine unless explicitly requested. |
| NATS / Kafka / IBM MQ | Treat brokers as project-owned or owner-provided dependencies unless the release explicitly supports provisioning. Use small Testcontainers only when needed and cap memory. |
| SOAP / gRPC mock | Use the WireMock-backed mock samples and boundary/failure sample suites before writing new shapes. |
| Common verification | Use `common_verify`, `artifact_compare`, or `polling_observer` for JSON/schema/file comparisons and observation polling. Polling must not retry mutating execute actions. |
| Contract-only providers | Validate contracts and report blocked runtime support; do not present them as fully executable. |
| Deprecated aliases | Do not author new tests with deprecated provider aliases. |

## Project Provisioning

Project-owned provisioning belongs in the project or PI-run harness, not hidden inside framework release assets. If dependencies are required:

- Materialize project runtime data before invoking the framework.
- Write readiness evidence and cleanup evidence.
- Keep secrets in `env://...`, local secret stores, or redacted runtime files. Never commit raw credentials.
- Run modes in increasing blast radius: single provider, mock-only, JDBC-lightweight, mixed baseline.
- Separate three outcomes in reports: DSL/artifact validation, project provisioning, and framework runtime consumption.

For the local PI-run workspace, use:

```bash
python3 pirun/run_contract_baseline.py --framework-version <version> --mode nats-only
python3 pirun/run_contract_baseline.py --framework-version <version> --mode wiremock-only
python3 pirun/run_contract_baseline.py --framework-version <version> --mode jdbc-lightweight
python3 pirun/run_contract_baseline.py --framework-version <version> --mode full-contract-baseline
```

## Framework Acceptance Workflow

Use this only when the user asks to PI-run or accept a framework release.

1. Download or verify release assets into `artifacts/release-assets/release-assets-v<version>/`.
2. Extract the usage kit into `artifacts/usage-kits/usage-kit-v<version>/usage-kit/`.
3. Verify checksums/signatures:

```bash
python3 pirun/verify_release_assets.py --framework-version <version> --output-dir reports
```

4. Inspect function/provider coverage:

```bash
python3 pirun/inspect_usage_kit.py --framework-version <version> --output-dir reports
```

5. Run lightweight regression checks:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q pirun tests tools
```

6. Execute suite/provider samples selectively. Prefer `validate` and `run --dry-run` before full `run`.
7. Produce reports under `reports/` and classify each issue as:
   - framework issue
   - project provisioning issue
   - DSL/test artifact authoring issue
   - release packaging issue
   - environment/resource limitation

## Reporting Rules

When reporting results:

- State the exact version, asset path, usage-kit path, commands run, exit codes, and report files.
- Do not claim "all features tested" unless every supported provider type, command, DSL section, evidence/report path, and mixed suite claim was exercised or explicitly inspected with rationale.
- Distinguish supported, contract-only, deprecated, and unsupported provider status.
- Distinguish project provisioning success from framework runtime consumption.
- Include concrete next actions for framework fixes and project-side fixes separately when both exist.
