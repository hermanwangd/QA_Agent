# pi-run v0.2.3 Full Coverage Report

## Summary

- Planned suite count: `15`
- Planned command count: `45`
- Executed command count: `45`
- Unexpected failures: `0`
- Blocked row count: `21`

## Suite Results

| Suite | Command | Status | Exit Code |
|---|---|---:|---:|
| `samples/contract_baseline/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/contract_baseline/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/contract_baseline/suite_manifest.yaml` | `run` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `validate` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `run --dry-run` | `PASS` | 0 |
| `samples/provider_capability/compare/suite_manifest.yaml` | `run` | `PASS` | 0 |
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
| `ibm_mq` | `ephemeral` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/ephemeral is contract-only in this framework release |
| `ibm_mq` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/native is contract-only in this framework release |
| `kafka` | `ephemeral` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/ephemeral is contract-only in this framework release |
| `kafka` | `native` | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/native is contract-only in this framework release |
| `external_runner` | `native` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `external_runner` | `stub` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `grpc_client` | `mock` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `grpc_client` | `stub` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `kubernetes_runtime` | `mock` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `kubernetes_runtime` | `native` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `polling_observer` | `ephemeral` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `rest_client` | `mock` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `rest_client` | `stub` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `mock` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `native` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `stub` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `vm_runtime` | `mock` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `vm_runtime` | `native` | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
