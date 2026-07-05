# pi-run v0.2.5 Full Coverage Report

## Summary

- Planned suite count: `36`
- Planned command count: `108`
- Executed command count: `108`
- Unexpected failures: `0`
- Blocked row count: `14`

## Suite Results

| Suite | Command | Status | Exit Code |
|---|---|---:|---:|
| `samples/00-getting-started/golden_e2e/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/00-getting-started/golden_e2e/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/00-getting-started/golden_e2e/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/10-contract-baseline/mixed_wiremock_jdbc_nats/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/10-contract-baseline/mixed_wiremock_jdbc_nats/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/10-contract-baseline/mixed_wiremock_jdbc_nats/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/data/jdbc/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/data/jdbc/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/data/jdbc/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/rest_client_with_wiremock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/rest_client_with_wiremock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/rest_client_with_wiremock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/wiremock_http_mock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/wiremock_http_mock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/http/wiremock_http_mock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/ibm_mq/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/ibm_mq/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/ibm_mq/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka_ibm_mq_mixed/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka_ibm_mq_mixed/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/kafka_ibm_mq_mixed/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/nats/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/nats/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/messaging/nats/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/grpc_mock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/grpc_mock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/grpc_mock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/soap_mock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/soap_mock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/rpc/soap_mock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/artifact_compare/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/artifact_compare/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/artifact_compare/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/common_verify/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/common_verify/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/common_verify/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/polling_observer/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/polling_observer/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/20-provider-capability-p0/verification/polling_observer/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/30-cross-provider-groups/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/90-compatibility/dummy_rest/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/90-compatibility/dummy_rest/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/90-compatibility/dummy_rest/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/contract_baseline/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/contract_baseline/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/contract_baseline/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/golden_e2e/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/golden_e2e/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/golden_e2e/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/common_verify/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/common_verify/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/common_verify/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/dummy_rest/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/dummy_rest/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/dummy_rest/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/grpc_mock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/grpc_mock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/grpc_mock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/ibm_mq/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/ibm_mq/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/ibm_mq/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/jdbc/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/jdbc/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/jdbc/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/kafka/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/kafka/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/kafka/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/messaging_mixed/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/messaging_mixed/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/messaging_mixed/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/grpc_mock_grpc_client/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/rest_wiremock_http/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/mock_server_cross_verify/soap_mock_http_client/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/nats/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/nats/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/nats/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/polling/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/polling/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/polling/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/soap_mock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/soap_mock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/soap_mock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/wiremock/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/wiremock/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/wiremock/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/wiremock_http_request/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/wiremock_http_request/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/wiremock_http_request/suite_manifest.yaml` | `run` | `PASS` | 0 |

## Blocked Rows

| Provider Type | Runtime Mode | Expected Status | Reason |
|---|---|---|---|
| `kafka_messaging` | `ephemeral` | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `mock` | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `native` | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `external_runner` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | external_runner/native is contract-only in this framework release |
| `external_runner` | `stub` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | external_runner/stub is contract-only in this framework release |
| `ibm_mq` | `ephemeral` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/ephemeral is contract-only in this framework release |
| `kafka` | `ephemeral` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/ephemeral is contract-only in this framework release |
| `kubernetes_runtime` | `mock` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kubernetes_runtime/mock is contract-only in this framework release |
| `kubernetes_runtime` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kubernetes_runtime/native is contract-only in this framework release |
| `shell_command` | `mock` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/mock is contract-only in this framework release |
| `shell_command` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/native is contract-only in this framework release |
| `shell_command` | `stub` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/stub is contract-only in this framework release |
| `vm_runtime` | `mock` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | vm_runtime/mock is contract-only in this framework release |
| `vm_runtime` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | vm_runtime/native is contract-only in this framework release |
