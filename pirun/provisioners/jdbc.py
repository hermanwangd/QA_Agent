from __future__ import annotations

from dataclasses import dataclass


@dataclass
class JdbcProvisionResult:
    provider_id: str
    provider_type: str
    runtime_mode: str
    provisioner: str
    dialect: str
    connection_secret_ref: str
    container_id: str | None
    readiness_status: str


def start_jdbc_lightweight(
    run_id: str,
    *,
    provider_id: str = "oracle-like-db",
    dialect: str = "oracle",
) -> JdbcProvisionResult:
    del run_id
    return JdbcProvisionResult(
        provider_id=provider_id,
        provider_type="jdbc",
        runtime_mode="ephemeral",
        provisioner="framework_embedded_h2",
        dialect=dialect,
        connection_secret_ref=f"generated://provider-capability/{dialect}-like/connection",
        container_id=None,
        readiness_status="delegated_to_framework",
    )
