from __future__ import annotations

import json
import shutil
from typing import Optional
from pathlib import Path

import yaml

from pirun.framework_paths import DEFAULT_FRAMEWORK_VERSION, usage_kit_samples_root


REPO_ROOT = Path(__file__).resolve().parents[2]
USAGE_KIT_SAMPLES = usage_kit_samples_root(DEFAULT_FRAMEWORK_VERSION, repo_root=REPO_ROOT)
NATS_SOURCE = USAGE_KIT_SAMPLES / "provider_capability" / "nats"
WIREMOCK_SOURCE = USAGE_KIT_SAMPLES / "provider_capability" / "wiremock"
JDBC_SOURCE = USAGE_KIT_SAMPLES / "provider_capability" / "jdbc"
CONTRACT_BASELINE_SOURCE = USAGE_KIT_SAMPLES / "contract_baseline"
NATS_PROVIDER_ID = "local-nats-event-bus"
WIREMOCK_PROVIDER_ID = "wiremock-payment-api"
JDBC_PROVIDER_ID = "oracle-like-db"


def materialize_nats_only(
    *,
    run_dir: Path,
    nats_subject: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    _copy_source(_source(samples_root, "provider_capability", "nats"), run_dir)

    _rename_profile_file(run_dir / "environment_bindings", "local_nats.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "env_profiles", "local_nats.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "execution_profiles", "local_nats.yaml", f"{profile}.yaml")

    suite_path = run_dir / "suite_manifest.yaml"
    test_case_path = run_dir / "test_case.yaml"
    provider_instance_path = run_dir / "provider_instances" / "local_nats.yaml"
    env_binding_path = run_dir / "environment_bindings" / f"{profile}.yaml"
    env_profile_path = run_dir / "env_profiles" / f"{profile}.yaml"
    execution_profile_path = run_dir / "execution_profiles" / f"{profile}.yaml"
    expected_path = run_dir / "expected_results" / "event_expected.json"

    suite = yaml.safe_load(suite_path.read_text()) or {}
    suite["profile"] = profile
    suite["purpose"] = "Project-provisioned Docker NATS capability verification POC."
    suite["evidence_policy"] = _local_evidence_policy()
    suite_path.write_text(yaml.safe_dump(suite, sort_keys=False), encoding="utf-8")

    test_case = yaml.safe_load(test_case_path.read_text()) or {}
    test_case["compatible_profiles"] = [profile]
    labels = test_case.setdefault("labels", {})
    labels["evidence_classification"] = "local_ci_ephemeral_only"
    labels["project_provisioned_dependency"] = "docker_nats"
    test_case_path.write_text(yaml.safe_dump(test_case, sort_keys=False), encoding="utf-8")

    provider_instance = yaml.safe_load(provider_instance_path.read_text()) or {}
    provider_instance["runtime_modes"] = ["ephemeral"]
    provider_instance.setdefault("labels", {})["evidence_classification"] = "local_ci_ephemeral_only"
    provider_instance_path.write_text(yaml.safe_dump(provider_instance, sort_keys=False), encoding="utf-8")

    expected = json.loads(expected_path.read_text())
    expected["subject"] = nats_subject
    expected_path.write_text(json.dumps(expected, indent=2), encoding="utf-8")

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-docker-nats"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": NATS_PROVIDER_ID,
            "provider_instance_ref": "provider_instances/local_nats.yaml",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": "env://PIRUN_NATS_CONNECTION"},
                "subject": nats_subject,
                "timeout": "PT5S",
                "poll_interval": "PT0.05S",
                "masking_policy": {"redact": ["connection", "password", "secret", "token", "authorization"]},
            },
        }
    ]
    env_binding["evidence_policy"] = {
        **_local_evidence_policy(),
    }
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["env_profile_id"] = profile
    env_profile["dependency_policy"] = {
        "require_readiness_evidence": True,
        "allow_framework_managed_dependencies": False,
    }
    env_profile["dependency_substitution_policy"] = {"allowed_runtime_modes": ["ephemeral"]}
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "project_tcp_connect",
        "cleanup_scope": "project_finally",
    }
    env_profile["providers"] = {
        NATS_PROVIDER_ID: {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": "env://PIRUN_NATS_CONNECTION"},
                "subject": {"value": nats_subject},
                "timeout": {"value": "PT5S"},
                "poll_interval": {"value": "PT0.05S"},
                "masking_policy": {"value": {"redact": ["connection", "password", "secret", "token", "authorization"]}},
            },
        }
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")

    execution_profile = yaml.safe_load(execution_profile_path.read_text()) or {}
    execution_profile["profile_id"] = profile
    execution_profile["environment_binding_ref"] = f"environment_bindings/{profile}.yaml"
    execution_profile["dependency_policy"] = {
        "require_readiness_evidence": True,
        "allow_framework_managed_dependencies": False,
    }
    execution_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "dependency_types": ["nats_event_bus"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "tcp_connect",
        "cleanup_scope": "project_finally",
        "output_binding_keys": ["connection.secret_ref", "subject"],
    }
    execution_profile["evidence_policy"] = _local_evidence_policy()
    execution_profile_path.write_text(yaml.safe_dump(execution_profile, sort_keys=False), encoding="utf-8")


def materialize_wiremock_only(
    *,
    run_dir: Path,
    base_url: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    _copy_source(_source(samples_root, "provider_capability", "wiremock"), run_dir)
    _rename_profile_file(run_dir / "environment_bindings", "local_wiremock.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "env_profiles", "local_wiremock.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "execution_profiles", "local_wiremock.yaml", f"{profile}.yaml")

    suite_path = run_dir / "suite_manifest.yaml"
    test_case_path = run_dir / "test_case.yaml"
    provider_instance_path = run_dir / "provider_instances" / "wiremock_payment_api.yaml"
    env_binding_path = run_dir / "environment_bindings" / f"{profile}.yaml"
    env_profile_path = run_dir / "env_profiles" / f"{profile}.yaml"
    execution_profile_path = run_dir / "execution_profiles" / f"{profile}.yaml"

    _write_suite_policy(
        suite_path,
        profile=profile,
        purpose="Project-provisioned Docker WireMock capability verification POC.",
    )
    _write_test_labels(test_case_path, profile=profile, dependency="docker_wiremock")
    _write_provider_labels(provider_instance_path)

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-docker-wiremock"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": WIREMOCK_PROVIDER_ID,
            "provider_instance_ref": "provider_instances/wiremock_payment_api.yaml",
            "runtime_mode": "mock",
            "binding_values": {
                "port_strategy": "dynamic",
                "mappings_ref": "fixtures/",
            },
        }
    ]
    env_binding["evidence_policy"] = _local_evidence_policy()
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["env_profile_id"] = profile
    env_profile["dependency_policy"] = {
        "require_readiness_evidence": True,
        "allow_framework_managed_dependencies": False,
    }
    env_profile["dependency_substitution_policy"] = {"allowed_runtime_modes": ["mock"]}
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "project_http_get",
        "cleanup_scope": "project_finally",
    }
    env_profile["providers"] = {
        WIREMOCK_PROVIDER_ID: {
            "runtime_mode": "mock",
            "binding_keys": {
                "port_strategy": {"value": "dynamic"},
                "mappings_ref": {"ref": "fixtures/"},
            },
        }
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")

    execution_profile = yaml.safe_load(execution_profile_path.read_text()) or {}
    execution_profile["profile_id"] = profile
    execution_profile["environment_binding_ref"] = f"environment_bindings/{profile}.yaml"
    execution_profile["dependency_policy"] = {
        "require_readiness_evidence": True,
        "allow_framework_managed_dependencies": False,
    }
    execution_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "dependency_types": ["wiremock_http_mock"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "http_get",
        "cleanup_scope": "project_finally",
        "output_binding_keys": ["base_url"],
    }
    execution_profile["evidence_policy"] = _local_evidence_policy()
    execution_profile_path.write_text(yaml.safe_dump(execution_profile, sort_keys=False), encoding="utf-8")
    _write_project_binding(
        run_dir,
        provider_id=WIREMOCK_PROVIDER_ID,
        provider_type="wiremock_http_mock",
        values={"base_url": base_url},
        framework_consumption_status="external_base_url_not_consumed_by_framework_provider_capability",
    )


def materialize_jdbc_lightweight(
    *,
    run_dir: Path,
    connection_secret_ref: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    _copy_source(_source(samples_root, "provider_capability", "jdbc"), run_dir)
    _rename_profile_file(run_dir / "environment_bindings", "local_jdbc.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "env_profiles", "local_jdbc.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "execution_profiles", "local_jdbc.yaml", f"{profile}.yaml")

    suite_path = run_dir / "suite_manifest.yaml"
    test_case_path = run_dir / "test_case.yaml"
    provider_instance_path = run_dir / "provider_instances" / "oracle_like.yaml"
    env_binding_path = run_dir / "environment_bindings" / f"{profile}.yaml"
    env_profile_path = run_dir / "env_profiles" / f"{profile}.yaml"
    execution_profile_path = run_dir / "execution_profiles" / f"{profile}.yaml"

    _write_suite_policy(
        suite_path,
        profile=profile,
        purpose="Project-selected lightweight JDBC/H2 capability verification POC.",
    )
    _write_test_labels(test_case_path, profile=profile, dependency="framework_embedded_h2")
    _write_provider_labels(provider_instance_path)

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-jdbc-lightweight"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": JDBC_PROVIDER_ID,
            "provider_instance_ref": "provider_instances/oracle_like.yaml",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": connection_secret_ref},
                "dialect": "oracle",
                "schema": "PUBLIC",
                "strict_params": True,
                "query_timeout": "PT10S",
                "masking_policy": {"redact": ["connection", "password", "secret", "token"]},
            },
        },
        {
            "provider_id": "db2-like-db",
            "provider_instance_ref": "provider_instances/db2_like.yaml",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": "generated://provider-capability/db2-like/connection"},
                "dialect": "db2",
                "schema": "PUBLIC",
                "strict_params": True,
                "query_timeout": "PT10S",
                "masking_policy": {"redact": ["connection", "password", "secret", "token"]},
            },
        }
    ]
    env_binding["evidence_policy"] = _local_evidence_policy()
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["env_profile_id"] = profile
    env_profile["dependency_policy"] = {
        "require_readiness_evidence": False,
        "allow_framework_managed_dependencies": True,
    }
    env_profile["dependency_substitution_policy"] = {"allowed_runtime_modes": ["ephemeral"]}
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["framework_embedded_h2"],
        "startup_policy": "framework_runtime",
        "readiness_policy": "framework_runtime",
        "cleanup_scope": "framework_runtime",
    }
    env_profile["providers"] = {
        JDBC_PROVIDER_ID: {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": connection_secret_ref},
                "dialect": {"value": "oracle"},
                "schema": {"value": "PUBLIC"},
                "strict_params": {"value": True},
                "query_timeout": {"value": "PT10S"},
                "masking_policy": {"value": {"redact": ["connection", "password", "secret", "token"]}},
            },
        },
        "db2-like-db": {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": "generated://provider-capability/db2-like/connection"},
                "dialect": {"value": "db2"},
                "schema": {"value": "PUBLIC"},
                "strict_params": {"value": True},
                "query_timeout": {"value": "PT10S"},
                "masking_policy": {"value": {"redact": ["connection", "password", "secret", "token"]}},
            },
        },
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")

    execution_profile = yaml.safe_load(execution_profile_path.read_text()) or {}
    execution_profile["profile_id"] = profile
    execution_profile["environment_binding_ref"] = f"environment_bindings/{profile}.yaml"
    execution_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["framework_embedded_h2"],
        "dependency_types": ["jdbc_h2_oracle_compat"],
        "startup_policy": "framework_runtime",
        "cleanup_scope": "framework_runtime",
    }
    execution_profile["evidence_policy"] = _local_evidence_policy()
    execution_profile_path.write_text(yaml.safe_dump(execution_profile, sort_keys=False), encoding="utf-8")


def materialize_heavy_jdbc_container(
    *,
    run_dir: Path,
    provider_id: str,
    dialect: str,
    connection_secret_ref: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    _copy_source(_source(samples_root, "provider_capability", "jdbc"), run_dir)
    _rename_profile_file(run_dir / "environment_bindings", "local_jdbc.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "env_profiles", "local_jdbc.yaml", f"{profile}.yaml")
    _rename_profile_file(run_dir / "execution_profiles", "local_jdbc.yaml", f"{profile}.yaml")

    suite_path = run_dir / "suite_manifest.yaml"
    test_case_path = run_dir / "test_case.yaml"
    env_binding_path = run_dir / "environment_bindings" / f"{profile}.yaml"
    env_profile_path = run_dir / "env_profiles" / f"{profile}.yaml"
    execution_profile_path = run_dir / "execution_profiles" / f"{profile}.yaml"
    provider_instance_ref = _jdbc_provider_instance_ref(dialect)
    provider_instance_path = run_dir / provider_instance_ref

    _write_suite_policy(
        suite_path,
        profile=profile,
        purpose=f"Project-provisioned Docker {dialect.upper()} JDBC capability verification.",
    )
    _write_test_labels(test_case_path, profile=profile, dependency=f"docker_jdbc_{dialect}")
    _retarget_heavy_jdbc_test_case(run_dir, provider_id=provider_id, dialect=dialect)
    _write_heavy_jdbc_sql(run_dir, dialect=dialect)
    if provider_instance_path.exists():
        _write_provider_labels(provider_instance_path)

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-docker-jdbc-{dialect}"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": provider_id,
            "provider_instance_ref": provider_instance_ref,
            "runtime_mode": "native",
            "binding_values": {
                "connection": {"secret_ref": connection_secret_ref},
                "dialect": dialect,
                "schema": "APP" if dialect == "oracle" else "DB2INST1",
                "strict_params": True,
                "query_timeout": "PT10S",
                "masking_policy": {"redact": ["connection", "password", "secret", "token"]},
            },
        }
    ]
    env_binding["evidence_policy"] = _local_evidence_policy()
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["env_profile_id"] = profile
    env_profile["dependency_policy"] = {
        "require_readiness_evidence": True,
        "allow_framework_managed_dependencies": False,
    }
    env_profile["dependency_substitution_policy"] = {"allowed_runtime_modes": ["native"]}
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "project_sql_probe",
        "cleanup_scope": "project_finally",
    }
    env_profile["providers"] = {
        provider_id: {
            "runtime_mode": "native",
            "binding_keys": {
                "connection": {"secret_ref": connection_secret_ref},
                "dialect": {"value": dialect},
                "schema": {"value": "APP" if dialect == "oracle" else "DB2INST1"},
                "strict_params": {"value": True},
                "query_timeout": {"value": "PT10S"},
                "masking_policy": {"value": {"redact": ["connection", "password", "secret", "token"]}},
            },
        }
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")

    execution_profile = yaml.safe_load(execution_profile_path.read_text()) or {}
    execution_profile["profile_id"] = profile
    execution_profile["environment_binding_ref"] = f"environment_bindings/{profile}.yaml"
    execution_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "dependency_types": [f"jdbc_{dialect}_container"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "project_sql_probe",
        "cleanup_scope": "project_finally",
        "output_binding_keys": ["connection.secret_ref", "dialect", "schema"],
    }
    execution_profile["evidence_policy"] = _local_evidence_policy()
    execution_profile_path.write_text(yaml.safe_dump(execution_profile, sort_keys=False), encoding="utf-8")

    _write_project_binding(
        run_dir,
        provider_id=provider_id,
        provider_type="jdbc",
        values={"connection": {"secret_ref": connection_secret_ref}, "dialect": dialect},
        framework_consumption_status="pending_framework_execution",
    )


def materialize_heavy_jdbc_crud_container(
    *,
    run_dir: Path,
    provider_id: str,
    dialect: str,
    connection_secret_ref: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    materialize_heavy_jdbc_container(
        run_dir=run_dir,
        provider_id=provider_id,
        dialect=dialect,
        connection_secret_ref=connection_secret_ref,
        profile=profile,
        samples_root=samples_root,
    )
    _retarget_heavy_jdbc_crud_test_case(run_dir, provider_id=provider_id, dialect=dialect)
    _write_heavy_jdbc_crud_sql(run_dir, dialect=dialect)


def materialize_full_contract_baseline(
    *,
    run_dir: Path,
    nats_connection_secret_ref: str,
    wiremock_base_url: str,
    jdbc_connection_secret_ref: str,
    profile: str = "ci",
    samples_root: Optional[Path] = None,
) -> None:
    _copy_source(_source(samples_root, "contract_baseline"), run_dir)
    suite_path = run_dir / "suite_manifest.yaml"
    test_case_path = run_dir / "test_case.yaml"
    env_binding_path = run_dir / "environment_bindings" / f"{profile}.yaml"
    env_profile_path = run_dir / "env_profiles" / f"{profile}.yaml"

    _write_suite_policy(
        suite_path,
        profile=profile,
        purpose="Project-materialized full contract baseline with NATS, WireMock, and lightweight JDBC.",
    )
    _write_test_labels(test_case_path, profile=profile, dependency="docker_wiremock+docker_nats+framework_embedded_h2")

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-full-contract-baseline"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": "wiremock-payment-api",
            "provider_instance_ref": "provider_instances/wiremock_payment_api.yaml",
            "runtime_mode": "mock",
            "binding_values": {
                "port_strategy": "dynamic",
                "mappings_ref": "fixtures/wiremock/payment-api/",
            },
        },
        {
            "provider_id": "oracle-database",
            "provider_instance_ref": "provider_instances/oracle_database.yaml",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": jdbc_connection_secret_ref},
                "dialect": "oracle",
                "schema": "PUBLIC",
                "strict_params": True,
                "query_timeout": "PT10S",
            },
        },
        {
            "provider_id": "nats-event-bus",
            "provider_instance_ref": "provider_instances/nats_event_bus.yaml",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": nats_connection_secret_ref},
                "subject": "payments.accepted",
                "timeout": "PT5S",
                "poll_interval": "PT0.05S",
            },
        },
    ]
    env_binding["evidence_policy"] = _local_evidence_policy()
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["env_profile_id"] = profile
    env_profile["providers"] = {
        "wiremock-payment-api": {
            "runtime_mode": "mock",
            "binding_keys": {
                "port_strategy": {"value": "dynamic"},
                "mappings_ref": {"ref": "fixtures/wiremock/payment-api/"},
            },
        },
        "oracle-database": {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": jdbc_connection_secret_ref},
                "dialect": {"value": "oracle"},
                "schema": {"value": "PUBLIC"},
                "strict_params": {"value": True},
                "query_timeout": {"value": "PT10S"},
            },
        },
        "nats-event-bus": {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": nats_connection_secret_ref},
                "subject": {"value": "payments.accepted"},
                "timeout": {"value": "PT5S"},
                "poll_interval": {"value": "PT0.05S"},
            },
        },
    }
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker", "framework_embedded_h2"],
        "startup_policy": "project_before_framework",
        "cleanup_scope": "project_finally",
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")

    _ensure_full_contract_fixtures(run_dir)
    _write_project_binding(
        run_dir,
        provider_id="wiremock-payment-api",
        provider_type="wiremock_http_mock",
        values={"base_url": wiremock_base_url},
        framework_consumption_status="external_base_url_not_consumed_by_framework_provider_capability",
    )


def _copy_source(source: Path, run_dir: Path) -> None:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(source, run_dir)


def _source(samples_root: Optional[Path], *parts: str) -> Path:
    return (samples_root or USAGE_KIT_SAMPLES).joinpath(*parts)


def _local_evidence_policy() -> dict:
    return {
        "evidence_classification": "local_ci_ephemeral_only",
        "downstream_release_evidence": False,
    }


def _write_suite_policy(suite_path: Path, *, profile: str, purpose: str) -> None:
    suite = yaml.safe_load(suite_path.read_text()) or {}
    suite["profile"] = profile
    suite["purpose"] = purpose
    suite["evidence_policy"] = _local_evidence_policy()
    suite_path.write_text(yaml.safe_dump(suite, sort_keys=False), encoding="utf-8")


def _write_test_labels(test_case_path: Path, *, profile: str, dependency: str) -> None:
    test_case = yaml.safe_load(test_case_path.read_text()) or {}
    test_case["compatible_profiles"] = [profile]
    labels = test_case.setdefault("labels", {})
    labels["evidence_classification"] = "local_ci_ephemeral_only"
    labels["downstream_release_evidence"] = False
    labels["project_provisioned_dependency"] = dependency
    test_case_path.write_text(yaml.safe_dump(test_case, sort_keys=False), encoding="utf-8")


def _retarget_heavy_jdbc_test_case(run_dir: Path, *, provider_id: str, dialect: str) -> None:
    test_case_path = run_dir / "test_case.yaml"
    test_case = yaml.safe_load(test_case_path.read_text()) or {}
    target_key = "db2_like_db" if dialect == "db2" else "oracle_like_db"
    query_name = f"order_exists_{dialect}.sql"
    query_operation_id = f"query_order_{dialect}"

    test_case["targets"] = {target_key: {"provider_id": provider_id}}
    for operation in test_case.get("setup", {}).get("operations", []):
        operation["target"] = target_key
    for operation in test_case.get("execute", {}).get("operations", []):
        operation["id"] = query_operation_id
        operation["target"] = target_key
        operation.setdefault("inputs", {}).setdefault("query_ref", {})["ref"] = f"queries/{query_name}"
    for check in test_case.get("verify", {}).get("checks", []):
        check["target"] = target_key
        check.setdefault("query", {})["ref"] = f"queries/{query_name}"
    for operation in test_case.get("cleanup", {}).get("operations", []):
        operation["target"] = target_key
    test_case.setdefault("evidence", {})["required"] = [
        f"provider-evidence/jdbc/query_{query_operation_id}.yaml",
        "provider-evidence/jdbc/seed_seed_order.yaml",
        "provider-evidence/jdbc/cleanup_cleanup_order.yaml",
    ]

    test_case_path.write_text(yaml.safe_dump(test_case, sort_keys=False), encoding="utf-8")


def _write_heavy_jdbc_sql(run_dir: Path, *, dialect: str) -> None:
    seed_path = run_dir / "fixtures" / "db_seed.sql"
    if dialect == "oracle":
        seed_path.write_text(
            "\n".join(
                [
                    "merge into ORDERS t",
                    "using (select :order_id ORDER_ID, 'READY' STATUS from dual) s",
                    "on (t.ORDER_ID = s.ORDER_ID)",
                    "when matched then update set t.STATUS = s.STATUS",
                    "when not matched then insert (ORDER_ID, STATUS) values (s.ORDER_ID, s.STATUS)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return
    if dialect == "db2":
        seed_path.write_text(
            "\n".join(
                [
                    "merge into ORDERS as t",
                    "using (values (cast(:order_id as varchar(64)), cast('READY' as varchar(32)))) as s(ORDER_ID, STATUS)",
                    "on t.ORDER_ID = s.ORDER_ID",
                    "when matched then update set STATUS = s.STATUS",
                    "when not matched then insert (ORDER_ID, STATUS) values (s.ORDER_ID, s.STATUS)",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return
    raise ValueError(f"unsupported heavy JDBC dialect: {dialect}")


def _retarget_heavy_jdbc_crud_test_case(run_dir: Path, *, provider_id: str, dialect: str) -> None:
    test_case_path = run_dir / "test_case.yaml"
    test_case = yaml.safe_load(test_case_path.read_text()) or {}
    target_key = "db2_like_db" if dialect == "db2" else "oracle_like_db"
    query_name = f"crud_order_by_id_{dialect}.sql"

    test_case["test_case_id"] = "JDBC-CRUD-TC-001"
    test_case["title"] = f"JDBC {dialect.upper()} explicit CRUD provider capability"
    test_case["targets"] = {target_key: {"provider_id": provider_id}}
    test_case["data"] = {
        "crud_insert": {"ref": "fixtures/crud_insert_order.sql"},
        "crud_update": {"ref": "fixtures/crud_update_order.sql"},
        "crud_delete": {"ref": "fixtures/crud_delete_order.sql"},
        "crud_query": {"ref": f"queries/{query_name}"},
        "crud_expected": {"ref": "expected_results/crud_expected.json"},
        "crud_deleted_expected": {"ref": "expected_results/crud_deleted_expected.json"},
    }
    test_case.pop("setup", None)
    test_case["execute"] = {
        "operations": [
            _crud_sql_operation("create_order", target_key, "db_seed", "${data.crud_insert}"),
            _crud_query_operation("read_created_order", target_key, query_name),
            _crud_sql_operation("update_order", target_key, "db_seed", "${data.crud_update}"),
            _crud_query_operation("read_updated_order", target_key, query_name),
            _crud_sql_operation("delete_order", target_key, "db_cleanup", "${data.crud_delete}"),
            _crud_query_operation("read_deleted_order", target_key, query_name),
        ]
    }
    test_case["verify"] = {
        "checks": [
            {
                "id": "deleted_order_record_absent",
                "type": "db_record_exists",
                "target": target_key,
                "query": {"ref": f"queries/{query_name}"},
                "expected_ref": "expected_results/crud_deleted_expected.json",
                "options": {"timeout": "PT20S", "poll_interval": "PT2S"},
            }
        ]
    }
    test_case["cleanup"] = {
        "operations": [
            _crud_sql_operation("cleanup_order_safety", target_key, "db_cleanup", "${data.crud_delete}")
        ]
    }
    test_case["evidence"] = {
        "required": [
            "provider-evidence/jdbc/seed_create_order.yaml",
            "provider-evidence/jdbc/query_read_created_order.yaml",
            "provider-evidence/jdbc/seed_update_order.yaml",
            "provider-evidence/jdbc/query_read_updated_order.yaml",
            "provider-evidence/jdbc/cleanup_delete_order.yaml",
            "provider-evidence/jdbc/query_read_deleted_order.yaml",
        ]
    }
    test_case_path.write_text(yaml.safe_dump(test_case, sort_keys=False), encoding="utf-8")


def _crud_sql_operation(operation_id: str, target_key: str, operation: str, sql_ref: str) -> dict:
    return {
        "id": operation_id,
        "target": target_key,
        "operation": operation,
        "inputs": {
            "sql_ref": {"ref": sql_ref},
            "params.order_id": {"ref": "expected_results/crud_expected.json#/order_id"},
        },
        "outputs": {
            "affected_rows": "affected_rows",
            "duration_ms": "duration_ms",
        },
    }


def _crud_query_operation(operation_id: str, target_key: str, query_name: str) -> dict:
    return {
        "id": operation_id,
        "target": target_key,
        "operation": "db_query",
        "inputs": {
            "query_ref": {"ref": f"queries/{query_name}"},
            "params.order_id": {"ref": "expected_results/crud_expected.json#/order_id"},
        },
        "outputs": {
            "row_count": "row_count",
            "sample_rows": "sample_rows",
            "duration_ms": "duration_ms",
            "query_evidence_ref": "query_evidence_ref",
        },
    }


def _write_heavy_jdbc_crud_sql(run_dir: Path, *, dialect: str) -> None:
    expected_path = run_dir / "expected_results" / "crud_expected.json"
    expected_path.write_text(
        json.dumps(
            {
                "order_id": "ORD-CRUD-001",
                "created_status": "CREATED",
                "updated_status": "UPDATED",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    deleted_expected_path = run_dir / "expected_results" / "crud_deleted_expected.json"
    deleted_expected_path.write_text(
        json.dumps(
            {
                "order_id": "ORD-CRUD-001",
                "expected_row_count": 0,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    query_path = run_dir / "queries" / f"crud_order_by_id_{dialect}.sql"
    query_path.write_text("select ORDER_ID, STATUS from ORDERS where ORDER_ID = :order_id\n", encoding="utf-8")
    delete_path = run_dir / "fixtures" / "crud_delete_order.sql"
    delete_path.write_text("delete from ORDERS where ORDER_ID = :order_id\n", encoding="utf-8")

    insert_path = run_dir / "fixtures" / "crud_insert_order.sql"
    update_path = run_dir / "fixtures" / "crud_update_order.sql"
    if dialect == "oracle":
        insert_path.write_text(
            "insert into ORDERS (ORDER_ID, STATUS) values (:order_id, 'CREATED')\n",
            encoding="utf-8",
        )
        update_path.write_text(
            "update ORDERS set STATUS = 'UPDATED' where ORDER_ID = :order_id\n",
            encoding="utf-8",
        )
        return
    if dialect == "db2":
        insert_path.write_text(
            "insert into ORDERS (ORDER_ID, STATUS) values (cast(:order_id as varchar(64)), 'CREATED')\n",
            encoding="utf-8",
        )
        update_path.write_text(
            "update ORDERS set STATUS = 'UPDATED' where ORDER_ID = cast(:order_id as varchar(64))\n",
            encoding="utf-8",
        )
        return
    raise ValueError(f"unsupported heavy JDBC dialect: {dialect}")


def _write_provider_labels(provider_instance_path: Path) -> None:
    provider_instance = yaml.safe_load(provider_instance_path.read_text()) or {}
    labels = provider_instance.setdefault("labels", {})
    labels["evidence_classification"] = "local_ci_ephemeral_only"
    labels["downstream_release_evidence"] = False
    provider_instance_path.write_text(yaml.safe_dump(provider_instance, sort_keys=False), encoding="utf-8")


def _ensure_full_contract_fixtures(run_dir: Path) -> None:
    wiremock_dir = run_dir / "fixtures" / "wiremock" / "payment-api"
    wiremock_dir.mkdir(parents=True, exist_ok=True)
    mappings_path = wiremock_dir / "mappings.yaml"
    if not mappings_path.exists():
        mappings_path.write_text(
            yaml.safe_dump(
                {
                    "stubs": [
                        {
                            "id": "payment-success",
                            "request": {"method": "POST", "path": "/payments"},
                            "response": {"status": 202},
                        }
                    ]
                },
                sort_keys=False,
            ),
            encoding="utf-8",
        )

    sql_dir = run_dir / "fixtures" / "sql"
    sql_dir.mkdir(parents=True, exist_ok=True)
    query_path = sql_dir / "find_order.sql"
    if not query_path.exists():
        query_path.write_text(
            "SELECT order_id, status\nFROM orders\nWHERE order_id = :order_id\n",
            encoding="utf-8",
        )


def _write_project_binding(
    run_dir: Path,
    *,
    provider_id: str,
    provider_type: str,
    values: dict,
    framework_consumption_status: str,
) -> None:
    project_binding_dir = run_dir / "project_bindings"
    project_binding_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "provider_id": provider_id,
        "provider_type": provider_type,
        "binding_values": values,
        "framework_consumption_status": framework_consumption_status,
        "evidence_classification": "local_ci_ephemeral_only",
    }
    (project_binding_dir / f"{provider_id}.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False),
        encoding="utf-8",
    )


def _jdbc_provider_instance_ref(dialect: str) -> str:
    if dialect == "db2":
        return "provider_instances/db2_like.yaml"
    return "provider_instances/oracle_like.yaml"


def _rename_profile_file(directory: Path, old_name: str, new_name: str) -> None:
    old_path = directory / old_name
    new_path = directory / new_name
    if old_path == new_path or not old_path.exists():
        return
    if new_path.exists():
        new_path.unlink()
    old_path.rename(new_path)
