# pi-run v0.2.4 Function Coverage Matrix

Generated from release usage-kit assets only.

## Summary

- Source archive used: `false`
- Registry provider count: `18`
- Provider contract count: `18`
- Matrix row count: `37`
- Registry without contract: `none`
- Contracts without registry: `none`
- Present release verification commands: `run, validate`
- Missing release verification commands: `report, validate-evidence`

## Matrix

| Provider Type | Runtime Mode | Runtime Status | Contract | Direct Sample | Indirect Sample | Runnable | Expected Status | Reason |
|---|---|---|---:|---:|---:|---:|---|---|
| `artifact_compare` | `stub` | `supported` | yes | no | yes | yes | `PASS` | release usage-kit sample is present |
| `common_verify` | `stub` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `external_runner` | `native` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | external_runner/native is contract-only in this framework release |
| `external_runner` | `stub` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | external_runner/stub is contract-only in this framework release |
| `grpc_client` | `mock` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `grpc_client` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `grpc_client` | `stub` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `grpc_mock` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `ibm_mq` | `ephemeral` | `supported` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/ephemeral is contract-only in this framework release |
| `ibm_mq` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `ibm_mq` | `native` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `jdbc` | `ephemeral` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `jdbc` | `native` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `kafka` | `ephemeral` | `supported` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/ephemeral is contract-only in this framework release |
| `kafka` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `kafka` | `native` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `kafka_messaging` | `ephemeral` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `mock` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `native` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kubernetes_runtime` | `mock` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kubernetes_runtime/mock is contract-only in this framework release |
| `kubernetes_runtime` | `native` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kubernetes_runtime/native is contract-only in this framework release |
| `nats` | `ephemeral` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `nats` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `nats` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `polling_observer` | `ephemeral` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `polling_observer` | `stub` | `supported` | yes | no | yes | yes | `PASS` | release usage-kit sample is present |
| `rest_client` | `mock` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `rest_client` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `rest_client` | `stub` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `sample_fake_provider` | `stub` | `unsupported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `shell_command` | `mock` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/mock is contract-only in this framework release |
| `shell_command` | `native` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/native is contract-only in this framework release |
| `shell_command` | `stub` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | shell_command/stub is contract-only in this framework release |
| `soap_mock` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `vm_runtime` | `mock` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | vm_runtime/mock is contract-only in this framework release |
| `vm_runtime` | `native` | `contract_only` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | vm_runtime/native is contract-only in this framework release |
| `wiremock_http_mock` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
