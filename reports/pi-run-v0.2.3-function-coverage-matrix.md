# pi-run v0.2.3 Function Coverage Matrix

Generated from release usage-kit assets only.

## Summary

- Source archive used: `false`
- Registry provider count: `16`
- Provider contract count: `18`
- Matrix row count: `35`
- Registry without contract: `none`
- Contracts without registry: `common_verify, sample_fake_provider`
- Present release verification commands: `run, validate`
- Missing release verification commands: `report, validate-evidence`

## Matrix

| Provider Type | Runtime Mode | Runtime Status | Contract | Direct Sample | Indirect Sample | Runnable | Expected Status | Reason |
|---|---|---|---:|---:|---:|---:|---|---|
| `artifact_compare` | `stub` | `supported` | yes | no | yes | yes | `PASS` | release usage-kit sample is present |
| `external_runner` | `native` | `approved_escape_hatch_only` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `external_runner` | `stub` | `approved_escape_hatch_only` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `grpc_client` | `mock` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `grpc_client` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `grpc_client` | `stub` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `grpc_mock` | `mock` | `partial` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `ibm_mq` | `ephemeral` | `partial` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/ephemeral is contract-only in this framework release |
| `ibm_mq` | `mock` | `partial` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `ibm_mq` | `native` | `partial` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | ibm_mq/native is contract-only in this framework release |
| `jdbc` | `ephemeral` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `jdbc` | `native` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `kafka` | `ephemeral` | `partial` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/ephemeral is contract-only in this framework release |
| `kafka` | `mock` | `partial` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `kafka` | `native` | `partial` | yes | no | no | no | `BLOCKED_FRAMEWORK_CONTRACT_ONLY` | kafka/native is contract-only in this framework release |
| `kafka_messaging` | `ephemeral` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `mock` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kafka_messaging` | `native` | `deprecated_alias` | yes | no | no | no | `BLOCKED_DEPRECATED_ALIAS` | deprecated compatibility alias; new artifacts must use canonical provider type |
| `kubernetes_runtime` | `mock` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `kubernetes_runtime` | `native` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `nats` | `ephemeral` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `nats` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `nats` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `polling_observer` | `ephemeral` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `polling_observer` | `stub` | `supported` | yes | no | yes | yes | `PASS` | release usage-kit sample is present |
| `rest_client` | `mock` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `rest_client` | `native` | `supported` | yes | yes | no | yes | `PASS` | release usage-kit sample is present |
| `rest_client` | `stub` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `mock` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `native` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `shell_command` | `stub` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `soap_mock` | `mock` | `partial` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
| `vm_runtime` | `mock` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `vm_runtime` | `native` | `supported` | yes | no | no | no | `BLOCKED_USAGE_KIT_SAMPLE_GAP` | no direct or indirect usage-kit sample found for this provider |
| `wiremock_http_mock` | `mock` | `supported` | yes | yes | yes | yes | `PASS` | release usage-kit sample is present |
