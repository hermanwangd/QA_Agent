# PI-run v0.2.2 Exhaustive Matrix

Inventory count: 29
Suite commands: 87
Result gate commands: 210
Unexpected command failures: 0
Known report blockers: 2

## Suite Matrix

| Suite | Profile | Kind | Validate | Dry-run | Run |
|---|---|---|---:|---:|---:|
| samples/contract_baseline/suite_manifest.yaml | ci | contract-baseline | OK | OK | BLOCKED(expected) |
| samples/contract_baseline/suite_manifest.yaml | sit | contract-baseline | OK | OK | BLOCKED(expected) |
| samples/golden_e2e/suite_manifest.yaml | local_golden | positive-suite | OK | OK | OK |
| samples/provider_capability/common_verify/suite_manifest.yaml | local_verify | positive-suite | OK | OK | OK |
| samples/provider_capability/compare/suite_manifest.yaml | local_compare | positive-suite | OK | OK | OK |
| samples/provider_capability/grpc_mock/suite_manifest.yaml | local_grpc_mock | positive-suite | OK | OK | OK |
| samples/provider_capability/grpc_mock/suite_manifest_boundary.yaml | local_grpc_mock | boundary-suite | OK | OK | OK |
| samples/provider_capability/grpc_mock/suite_manifest_failure.yaml | local_grpc_mock | negative-suite | OK | OK | FAIL(expected) |
| samples/provider_capability/ibm_mq/suite_manifest.yaml | local_ibm_mq | positive-suite | OK | OK | OK |
| samples/provider_capability/jdbc/suite_manifest.yaml | local_jdbc | positive-suite | OK | OK | OK |
| samples/provider_capability/kafka/suite_manifest.yaml | local_kafka | positive-suite | OK | OK | OK |
| samples/provider_capability/messaging_mixed/suite_manifest.yaml | local_messaging | positive-suite | OK | OK | OK |
| samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml | local_grpc_mock | positive-suite | OK | OK | OK |
| samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest_failure.yaml | local_grpc_mock | negative-suite | OK | OK | FAIL(expected) |
| samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml | local_wiremock_http | positive-suite | OK | OK | OK |
| samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest_failure.yaml | local_wiremock_http | negative-suite | OK | OK | FAIL(expected) |
| samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml | local_soap_mock | positive-suite | OK | OK | OK |
| samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest_failure.yaml | local_soap_mock | negative-suite | OK | OK | FAIL(expected) |
| samples/provider_capability/mock_server_cross_verify/suite_manifest.yaml | local_mock_server_cross_verify | suite-group | OK | OK | OK |
| samples/provider_capability/nats/suite_manifest.yaml | local_nats | positive-suite | OK | OK | OK |
| samples/provider_capability/polling/suite_manifest.yaml | local_polling | positive-suite | OK | OK | OK |
| samples/provider_capability/soap_mock/suite_manifest.yaml | local_soap_mock | positive-suite | OK | OK | OK |
| samples/provider_capability/soap_mock/suite_manifest_boundary.yaml | local_soap_mock | boundary-suite | OK | OK | OK |
| samples/provider_capability/soap_mock/suite_manifest_failure.yaml | local_soap_mock | negative-suite | OK | OK | FAIL(expected) |
| samples/provider_capability/suite_manifest.yaml | local_provider | suite-group | OK | OK | OK |
| samples/provider_capability/wiremock/suite_manifest.yaml | local_wiremock | positive-suite | OK | OK | OK |
| samples/provider_capability/wiremock_http_request/suite_manifest.yaml | local_wiremock_http | positive-suite | OK | OK | OK |
| samples/provider_capability/wiremock_http_request/suite_manifest_boundary.yaml | local_wiremock_http | boundary-suite | OK | OK | OK |
| samples/provider_capability/wiremock_http_request/suite_manifest_failure.yaml | local_wiremock_http | negative-suite | OK | OK | FAIL(expected) |

## Unexpected Failures

- None

## Known Report Blockers

- `target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141003040-1/RUN-REST-20260704141003040-1/result.json`: `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`
- `target/provider-capability/rest_client/DUMMY-REST-PI-RUN-v0.2/BATCH-REST-20260704141208275-1/RUN-REST-20260704141208275-1/result.json`: `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`
