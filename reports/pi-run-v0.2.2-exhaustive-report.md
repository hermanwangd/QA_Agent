# PI-run v0.2.2 Exhaustive Executable Coverage Report

Date: 2026-07-04 Asia/Taipei

Scope: v0.2.2 GitHub release assets only. No source checkout was used.

Release source:

- https://github.com/hermanwangd/Auto_Regression_Test_Framework/releases/tag/v0.2.2

Artifacts produced by this run:

- `docs/superpowers/plans/2026-07-04-v022-exhaustive-pirun.md`
- `tools/run_v022_exhaustive_matrix.py`
- `reports/pi-run-v0.2.2-exhaustive-matrix.json`
- `reports/pi-run-v0.2.2-exhaustive-matrix.md`
- `reports/pi-run-v0.2.2-exhaustive-report.md`

All Java commands were run sequentially with `-Xmx512m`.

## Overall Verdict

The release-asset executable scope was exhaustively run.

Result:

- 29 suite/profile entries inventoried from `usage-kit-v0.2.2/usage-kit/samples`.
- 87 suite commands executed: `validate`, `run --dry-run`, and `run` for each entry.
- 210 result gate commands executed: `validate-evidence` and `report --format yaml` over generated/existing `result.json` evidence.
- 0 unexpected matrix failures.
- 2 known report blockers from previous custom REST results, plus the fresh custom REST result reproduced the same blocker.
- 3 evidence-hardening sample gates executed: valid result passed, missing evidence failed as expected, raw secret failed as expected.
- Release checksums and detached signatures verified.

This still cannot be honestly called "every framework feature fully certified" because several documented provider types have no executable sample in the release asset, and the v0.2.2 release jar does not expose an executable Testcontainers provisioning runtime for the documented future slices.

## Suite Matrix Summary

Matrix command:

```sh
python3 tools/run_v022_exhaustive_matrix.py --run-all
```

Summary:

```text
inventory_count: 29
suite_commands: 87
result_gate_commands: 210
unexpected_failures: 0
known_report_blockers: 2
```

Inventory by kind:

| Kind | Count | Meaning |
|---|---:|---|
| `positive-suite` | 16 | Normal suite expected to pass. |
| `negative-suite` | 6 | Suite expected to fail at runtime for negative verification coverage. |
| `boundary-suite` | 3 | Boundary-value suite expected to pass. |
| `suite-group` | 2 | Parent suite dispatch covering child suites. |
| `contract-baseline` | 2 | `contract_baseline` manifest run once for `ci` and once for `sit`. |

Full matrix:

- `reports/pi-run-v0.2.2-exhaustive-matrix.md`
- `reports/pi-run-v0.2.2-exhaustive-matrix.json`

## Covered Provider/Operation/Verify Surface

Provider types observed in executable sample provider instances:

- `common_verify`
- `grpc_client`
- `grpc_mock`
- `ibm_mq`
- `jdbc`
- `kafka`
- `nats`
- `rest_client`
- `sample_fake_provider`
- `soap_mock`
- `wiremock_http_mock`

Execute operations observed in test DSL:

- `db_query`
- `execute_sample`
- `grpc_request_received`
- `http_request`
- `kafka_publish`
- `mq_put`
- `nats_publish`
- `send_http_request`
- `soap_request_received`
- `unary_call`
- `verify_requests`

Verify types observed in test DSL:

- `db_record_exists`
- `event_payload_match`
- `event_published`
- `file_diff`
- `http_mock_called`
- `http_mock_request_body_match`
- `json_match`
- `kafka_payload_match`
- `mq_payload_match`
- `schema_match`
- `value_equals`

## Boundary And Negative Coverage

Boundary suites executed:

- `samples/provider_capability/grpc_mock/suite_manifest_boundary.yaml`
- `samples/provider_capability/soap_mock/suite_manifest_boundary.yaml`
- `samples/provider_capability/wiremock_http_request/suite_manifest_boundary.yaml`

Negative suites executed and failed as expected:

- `samples/provider_capability/grpc_mock/suite_manifest_failure.yaml`
- `samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest_failure.yaml`
- `samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest_failure.yaml`
- `samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest_failure.yaml`
- `samples/provider_capability/soap_mock/suite_manifest_failure.yaml`
- `samples/provider_capability/wiremock_http_request/suite_manifest_failure.yaml`

Their reports returned `report_status: review_ready_with_failures`, which is expected for negative verification samples.

## Parent Suite Coverage

`PROVIDER-CAPABILITY-P0-v0.2` was executed through the matrix and passed.

Previously observed direct summary evidence remains:

- `usage-kit-v0.2.2/usage-kit/target/suite-groups/PROVIDER-CAPABILITY-P0-v0.2/BATCH-MR6FWCOC/RUN-1b7a5655-9e4d-4404-b069-3afea99689b9/suite_summary.yaml`

Key status:

```yaml
status: passed
test_count: 12
passed_count: 12
failed_count: 0
unsupported_count: 0
blocked_count: 0
```

`MOCK-SERVER-CROSS-VERIFY-v0.2` was executed through the matrix and passed.

Previously observed direct summary evidence remains:

- `usage-kit-v0.2.2/usage-kit/target/suite-groups/MOCK-SERVER-CROSS-VERIFY-v0.2/BATCH-MR6FWKVN/RUN-3892e93a-4521-48ec-8df2-5e834f7b5927/suite_summary.yaml`

Key status:

```yaml
status: passed
test_count: 6
passed_count: 6
failed_count: 0
expected_failure_count: 3
expected_failed_observed_count: 3
unsupported_count: 0
blocked_count: 0
```

## Contract Baseline Result

`samples/contract_baseline/suite_manifest.yaml` was executed for both `ci` and `sit`.

Observed:

- `validate`: passed.
- `run --dry-run`: passed.
- `run`: blocked as expected by the current suite-mode runtime boundary.

Failure:

```yaml
run_status: blocked
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
```

Interpretation: the contract baseline remains useful as contract/DSL validation evidence, but it is not full executable PI-run evidence in v0.2.2.

## Custom Dummy REST PI-run

Fresh dummy REST result from this run:

- `target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704143843681-1/RUN-REST-20260704143843681-1/result.json`

Commands covered:

- `python3 -m unittest tests/test_dummy_app.py`: 4 tests passed.
- `validate --suite pi_run_demo/dummy_rest/suite_manifest.yaml --profile local_dummy`: passed.
- `pi-run --suite pi_run_demo/dummy_rest/suite_manifest.yaml --profile local_dummy --dry-run`: passed.
- `pi-run --suite pi_run_demo/dummy_rest/suite_manifest.yaml --profile local_dummy`: passed.
- `validate-evidence --result <fresh result>`: passed.
- `report --result <fresh result> --format yaml`: failed with the known blocker.

Fresh full run:

```yaml
run_status: passed
suite_id: DUMMY-REST-PI-RUN-v0.2
batch_id: BATCH-REST-20260704143843681-1
run_id: RUN-REST-20260704143843681-1
test_count: 1
passed_count: 1
failed_count: 0
provider_runtime_executed: true
provider_type: rest_client
provider_id: dummy-order-api
```

Fresh evidence validation:

```yaml
evidence_validation_status: passed
missing_evidence_count: 0
failed_evidence_count: 0
masking_status: passed
```

Fresh report blocker:

```yaml
report_status: invalid
failure_code: VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM
field_path: provider_results.release_evidence_eligible
owner_action: Mark contract-baseline provider results as framework evidence only.
```

Interpretation: custom native REST execution works, but custom native REST reporting is still not accepted.

## Evidence Hardening

| Sample | Expected | Observed |
|---|---|---|
| `samples/evidence_hardening/valid_result.json` | pass | `evidence_validation_status: passed` |
| `samples/evidence_hardening/invalid_missing_evidence_result.json` | fail | `EVIDENCE_MISSING_EVIDENCE_INDEX` |
| `samples/evidence_hardening/invalid_secret_leak_result.json` | fail | `SECRET_GUARDRAIL_RAW_SECRET` |

## Release Artifact Verification

Checksum command:

```sh
awk '{name=$2; sub(/^target\//, "", name); printf "%s  %s\n", $1, name}' checksums.sha256 | shasum -a 256 -c -
```

Observed:

```text
spec-driven-auto-regression-0.2.2.jar: OK
spec-driven-auto-regression-0.2.2-usage-kit.zip: OK
bom.json: OK
bom.xml: OK
```

Detached signature verification using each `.pem` public key and `.sig` file:

```text
spec-driven-auto-regression-0.2.2.jar: Verified OK
spec-driven-auto-regression-0.2.2-usage-kit.zip: Verified OK
bom.json: Verified OK
bom.xml: Verified OK
checksums.sha256: Verified OK
```

Note: `cosign` is not installed on this machine, so this is detached signature verification against the bundled certificate public key, not full Sigstore identity/transparency-log policy verification.

## CLI And Security Gates

CLI:

- `java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar --help`: exit 0.
- `java -Xmx512m -jar release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar`: exit 0 and printed usage.

Security:

- `release-assets-v0.2.2/dependency-check-report.json` was queried for dependencies with non-null `vulnerabilities`.
- No vulnerability rows were returned.

Resource:

```text
104726528 maximum resident set size
82346896 peak memory footprint
```

This is below the requested 8G machine safety limit.

## Testcontainers

Container runtime availability check:

```sh
command -v docker || true
command -v colima || true
command -v podman || true
command -v nerdctl || true
```

Initial observation: the active Codex shell `PATH` did not include `/usr/local/bin`, so `docker` was not found by bare command name.

Docker Desktop was installed at:

```text
/Applications/Docker.app
/usr/local/bin/docker -> /Applications/Docker.app/Contents/Resources/bin/docker
```

After starting Docker Desktop and using the full CLI path:

```text
client=28.4.0 server=28.4.0
server=28.4.0 os=linux cpus=8 mem=8218316800
```

With Docker ready, `samples/contract_baseline/suite_manifest.yaml` was rerun with profile `ci`:

```yaml
run_status: blocked
suite_id: RP-FWK-CONTRACT-SAMPLE-regression
provider_runtime_invoked: false
failure_code: CONTRACT_UNSUPPORTED_SUITE_RUNTIME
provider_type: jdbc,nats,wiremock_http_mock
owner_action: Use a provider type supported by SuiteRuntimeDispatcher or add an explicit runtime dispatcher path.
```

The v0.2.2 jar was also inspected for Testcontainers/docker-java runtime dependencies:

```sh
jar tf release-assets-v0.2.2/spec-driven-auto-regression-0.2.2.jar | rg -i 'testcontainers|docker-java'
```

Observed: no matching classes or bundled dependencies.

Therefore Testcontainers-based provider provisioning could not be executed from this v0.2.2 release jar even though Docker is available after starting Docker Desktop.

Even with Docker available, v0.2.2's provider support matrix states:

- `kafka` native and ephemeral modes are `contract-only`.
- `ibm_mq` native and ephemeral modes are `contract-only`.
- native broker and Testcontainer execution are future runtime slices.

So Testcontainers would not close Kafka/IBM MQ native runtime coverage for this v0.2.2 release jar unless the framework runtime itself is extended.

## Not Fully Covered

Documented provider types without an executable sample provider instance in the v0.2.2 usage kit:

- `artifact_compare`
- `external_runner`
- `kafka_messaging`
- `kubernetes_runtime`
- `polling_observer`
- `shell_command`
- `vm_runtime`

Notes:

- Artifact comparison behavior was exercised through the `compare` suite, but its sample provider type is `common_verify`, not `artifact_compare`.
- Polling behavior was exercised through the `polling` suite, but its sample provider type is `common_verify`, not `polling_observer`.
- `external_runner`, `shell_command`, `kubernetes_runtime`, and `vm_runtime` are documented provider types but have no release-asset executable sample in this usage kit.
- `kafka_messaging` is documented as deprecated.

## Final Decision

The v0.2.2 release-asset executable coverage has been run exhaustively.

Do not claim full framework feature certification yet.

Blocking or incomplete areas:

- custom native REST `report --format yaml` fails with `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`;
- `contract_baseline` validates and dry-runs but full run is blocked by `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`;
- several documented provider types have no executable sample in the release asset;
- Docker is available after starting Docker Desktop, but Testcontainers provider provisioning is not executable from the v0.2.2 release jar;
- Kafka/IBM MQ native/Testcontainer execution is documented as future/contract-only in v0.2.2.
