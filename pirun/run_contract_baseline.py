from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.docker_cli import remove_by_label
from pirun.framework_paths import (
    DEFAULT_FRAMEWORK_VERSION,
    FrameworkPaths,
    framework_paths as resolve_framework_paths,
)
from pirun.materialize.contract_baseline import (
    materialize_full_contract_baseline,
    materialize_jdbc_lightweight,
    materialize_nats_only,
    materialize_wiremock_only,
)
from pirun.provisioners.jdbc import JdbcProvisionResult, start_jdbc_lightweight
from pirun.provisioners.nats import NatsProvisionResult, start_nats
from pirun.provisioners.wiremock import WireMockProvisionResult, start_wiremock
from pirun.redaction import redact_text


REPO_ROOT = Path(__file__).resolve().parents[1]
MODE_SEQUENCE = ("nats-only", "wiremock-only", "jdbc-lightweight", "full-contract-baseline")
MODE_SUITE_DIRS = {
    "nats-only": "nats_capability",
    "wiremock-only": "wiremock_capability",
    "jdbc-lightweight": "jdbc_capability",
    "full-contract-baseline": "contract_baseline",
}


class ProvisioningError(RuntimeError):
    def __init__(self, message: str, *, dependencies: list[dict], failed_step: str):
        super().__init__(message)
        self.dependencies = list(dependencies)
        self.failed_step = failed_step


def run_root_for_mode(run_id: str, mode: str) -> Path:
    return REPO_ROOT / ".pirun" / "runs" / run_id / MODE_SUITE_DIRS[mode]


def framework_paths(version: str) -> FrameworkPaths:
    return resolve_framework_paths(version, repo_root=REPO_ROOT)


def _default_usage_kit_root() -> Path:
    return framework_paths(DEFAULT_FRAMEWORK_VERSION).usage_kit_root


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="ci")
    parser.add_argument("--mode", choices=MODE_SEQUENCE, default="nats-only")
    parser.add_argument("--run-id", default=f"PIRUN-{int(time.time())}")
    parser.add_argument("--framework-version", default=DEFAULT_FRAMEWORK_VERSION)
    args = parser.parse_args()

    paths = framework_paths(args.framework_version)
    run_root = run_root_for_mode(args.run_id, args.mode)
    dependencies = []
    framework = {"invoked": False}
    cleanup = {"status": "not_started"}
    orchestration_error = None
    failed_step = None
    exit_code = 1

    try:
        env = os.environ.copy()
        dependencies, env_updates = prepare_mode(
            args.mode,
            args.run_id,
            args.profile,
            run_root,
            samples_root=paths.samples_root,
        )
        env.update(env_updates)
        cmd = [
            "java",
            "-Xmx512m",
            "-jar",
            str(paths.jar),
            "run",
            "--suite",
            str(run_root / "suite_manifest.yaml"),
            "--profile",
            args.profile,
        ]
        proc = subprocess.run(
            cmd,
            cwd=str(paths.usage_kit_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        framework = {
            "invoked": True,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        exit_code = proc.returncode
    except ProvisioningError as exc:
        dependencies = exc.dependencies
        failed_step = exc.failed_step
        orchestration_error = str(exc)
        exit_code = 1
    except Exception as exc:
        orchestration_error = str(exc)
        exit_code = 1
    finally:
        try:
            cleanup_result = remove_by_label(args.run_id)
            if cleanup_result.exit_code != 0:
                raise RuntimeError(cleanup_result.stderr.strip())
            cleanup = {"status": "passed"}
        except Exception as exc:
            cleanup = {"status": "failed", "error": str(exc)}
            exit_code = 1
        write_project_report(
            args.run_id,
            args.profile,
            args.mode,
            run_root,
            dependencies,
            framework,
            cleanup,
            orchestration_error,
            failed_step,
            usage_kit_root=paths.usage_kit_root,
        )

    return exit_code


def prepare_mode(
    mode: str,
    run_id: str,
    profile: str,
    run_root: Path,
    *,
    samples_root: Path | None = None,
) -> tuple[list[dict], dict[str, str]]:
    if mode == "nats-only":
        dependencies = []
        step = "start_nats"
        try:
            nats = start_nats(run_id, provider_id="local-nats-event-bus", suite="nats_capability")
            dependencies.append(_nats_dependency(nats))
            step = "materialize_nats_only"
            materialize_nats_only(
                run_dir=run_root,
                nats_subject="orders.ready",
                profile=profile,
                samples_root=samples_root,
            )
            return dependencies, {"PIRUN_NATS_CONNECTION": nats.connection_url}
        except Exception as exc:
            raise ProvisioningError(str(exc), dependencies=dependencies, failed_step=step) from exc

    if mode == "wiremock-only":
        dependencies = []
        step = "start_wiremock"
        try:
            wiremock = start_wiremock(run_id, provider_id="wiremock-payment-api", suite="wiremock_capability")
            dependencies.append(_wiremock_dependency(wiremock))
            step = "materialize_wiremock_only"
            materialize_wiremock_only(
                run_dir=run_root,
                base_url=wiremock.base_url,
                profile=profile,
                samples_root=samples_root,
            )
            return dependencies, {}
        except Exception as exc:
            raise ProvisioningError(str(exc), dependencies=dependencies, failed_step=step) from exc

    if mode == "jdbc-lightweight":
        dependencies = []
        step = "start_jdbc_lightweight"
        try:
            jdbc = start_jdbc_lightweight(run_id)
            dependencies.append(_jdbc_dependency(jdbc))
            step = "materialize_jdbc_lightweight"
            materialize_jdbc_lightweight(
                run_dir=run_root,
                connection_secret_ref=jdbc.connection_secret_ref,
                profile=profile,
                samples_root=samples_root,
            )
            return dependencies, {}
        except Exception as exc:
            raise ProvisioningError(str(exc), dependencies=dependencies, failed_step=step) from exc

    if mode == "full-contract-baseline":
        dependencies = []
        step = "start_nats"
        try:
            nats = start_nats(run_id, provider_id="nats-event-bus", suite="contract_baseline")
            dependencies.append(_nats_dependency(nats))
            step = "start_wiremock"
            wiremock = start_wiremock(run_id, provider_id="wiremock-payment-api", suite="contract_baseline")
            dependencies.append(_wiremock_dependency(wiremock))
            step = "start_jdbc_lightweight"
            jdbc = start_jdbc_lightweight(run_id, provider_id="oracle-database")
            dependencies.append(_jdbc_dependency(jdbc))
            step = "materialize_full_contract_baseline"
            materialize_full_contract_baseline(
                run_dir=run_root,
                nats_connection_secret_ref="env://PIRUN_NATS_CONNECTION",
                wiremock_base_url=wiremock.base_url,
                jdbc_connection_secret_ref=jdbc.connection_secret_ref,
                profile=profile,
                samples_root=samples_root,
            )
            return dependencies, {"PIRUN_NATS_CONNECTION": nats.connection_url}
        except Exception as exc:
            raise ProvisioningError(str(exc), dependencies=dependencies, failed_step=step) from exc

    raise ValueError(f"unsupported mode: {mode}")


def _nats_dependency(nats: NatsProvisionResult) -> dict:
    return {
        "provider_id": nats.provider_id,
        "provider_type": "nats",
        "provisioner": "project_docker",
        "image": nats.image,
        "container_id": nats.container_id,
        "mapped_ports": {"4222": nats.port},
        "readiness": {"status": nats.readiness_status, "check": "tcp_connect"},
    }


def _wiremock_dependency(wiremock: WireMockProvisionResult) -> dict:
    return {
        "provider_id": wiremock.provider_id,
        "provider_type": "wiremock_http_mock",
        "provisioner": "project_docker",
        "image": wiremock.image,
        "container_id": wiremock.container_id,
        "mapped_ports": {"8080": wiremock.port},
        "base_url": wiremock.base_url,
        "readiness": {"status": wiremock.readiness_status, "check": "http_get"},
    }


def _jdbc_dependency(jdbc: JdbcProvisionResult) -> dict:
    return {
        "provider_id": jdbc.provider_id,
        "provider_type": jdbc.provider_type,
        "runtime_mode": jdbc.runtime_mode,
        "provisioner": jdbc.provisioner,
        "dialect": jdbc.dialect,
        "connection_secret_ref": jdbc.connection_secret_ref,
        "container_id": jdbc.container_id,
        "readiness": {"status": jdbc.readiness_status, "check": "framework_embedded_h2"},
    }


def write_project_report(
    run_id: str,
    profile: str,
    mode: str,
    run_root: Path,
    dependencies,
    framework,
    cleanup,
    orchestration_error,
    failed_step: str | None = None,
    usage_kit_root: Path | None = None,
) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    usage_kit_root = usage_kit_root or _default_usage_kit_root()
    stdout = framework.get("stdout", "")
    result_json = _result_json_from_stdout(stdout, usage_kit_root=usage_kit_root)
    result_payload, result_json_parse_error = _load_result_json(result_json)
    failure_codes = _failure_codes(stdout, result_payload)
    report_dependencies = _dependencies_with_framework_consumption(mode, dependencies, framework, failure_codes)
    known_blockers = [
        "CONTRACT_UNSUPPORTED_SUITE_RUNTIME",
        "CONTRACT_UNKNOWN_PROVIDER_TYPE",
        "NATS_CONNECTION_FAILED",
        "Secret-ref backed NATS connection is not available",
    ]
    report = {
        "project_provisioning_report_version": "v0.1",
        "run_id": run_id,
        "profile": profile,
        "mode": mode,
        "suite": MODE_SUITE_DIRS[mode],
        "project_provisioning_status": "passed" if dependencies and not failed_step else "failed",
        "materialization_status": "passed" if (run_root / "suite_manifest.yaml").exists() else "failed",
        "framework_invoked": bool(framework.get("invoked")),
        "framework_result": {
            "exit_code": framework.get("exit_code"),
            "run_status": _extract_scalar(stdout, "run_status"),
            "provider_runtime_invoked": _extract_bool(stdout, "provider_runtime_invoked")
            or _extract_bool(stdout, "provider_runtime_executed"),
            "failure_codes": sorted(failure_codes),
            "failure_reason": (result_payload.get("failure") or {}).get("reason") if result_payload else None,
            "owner_action": (result_payload.get("failure") or {}).get("owner_action") if result_payload else None,
            "result_json": _report_path(result_json),
            "result_json_parse_error": result_json_parse_error,
            "known_blocker": any(blocker in stdout for blocker in known_blockers)
            or bool(failure_codes.intersection(known_blockers)),
        },
        "orchestration_error": orchestration_error,
        "failed_step": failed_step,
        "dependencies": report_dependencies,
        "framework_consumed_project_dependencies": any(
            dependency.get("framework_consumed") for dependency in report_dependencies
        ),
        "cleanup_status": cleanup["status"],
        "evidence_classification": "local_ci_ephemeral_only",
        "downstream_release_evidence": False,
    }
    (run_root / "provisioning_evidence.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    (run_root / "framework_stdout.txt").write_text(redact_text(framework.get("stdout", "")), encoding="utf-8")
    (run_root / "framework_stderr.txt").write_text(redact_text(framework.get("stderr", "")), encoding="utf-8")
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def _extract_scalar(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else None


def _extract_bool(text: str, key: str) -> bool:
    value = _extract_scalar(text, key)
    return value == "true"


def _result_json_from_stdout(text: str, *, usage_kit_root: Path | None = None) -> Path | None:
    result_ref = _extract_scalar(text, "result_json")
    if not result_ref:
        return None
    usage_kit_root = usage_kit_root or _default_usage_kit_root()
    path = Path(result_ref)
    if not path.is_absolute():
        path = usage_kit_root / path
    return path if path.exists() else None


def _report_path(path: Path | None) -> str | None:
    if not path:
        return None
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _load_result_json(path: Path | None) -> tuple[dict, str | None]:
    if not path:
        return {}, None
    try:
        return json.loads(path.read_text()), None
    except (OSError, json.JSONDecodeError) as exc:
        return {}, str(exc)


def _failure_codes(stdout: str, result_payload: dict) -> set[str]:
    codes = set(re.findall(r"failure_code:\s*([A-Z0-9_]+)", stdout))
    failure = result_payload.get("failure") or {}
    if failure.get("code"):
        codes.add(failure["code"])
    for result in result_payload.get("test_results", []):
        if result.get("failure_code"):
            codes.add(result["failure_code"])
    return codes


def _dependencies_with_framework_consumption(
    mode: str,
    dependencies: list[dict],
    framework: dict,
    failure_codes: set[str],
) -> list[dict]:
    return [
        {
            **dependency,
            **_framework_consumption(mode, dependency, framework, failure_codes),
        }
        for dependency in dependencies
    ]


def _framework_consumption(mode: str, dependency: dict, framework: dict, failure_codes: set[str]) -> dict:
    stdout = framework.get("stdout", "")
    runtime_executed = _extract_bool(stdout, "provider_runtime_invoked") or _extract_bool(
        stdout, "provider_runtime_executed"
    )
    if not framework.get("invoked"):
        return {"framework_consumed": False, "framework_consumption_status": "framework_not_invoked"}

    if mode == "wiremock-only" and dependency.get("provider_type") == "wiremock_http_mock":
        return {
            "framework_consumed": False,
            "framework_consumption_status": "external_base_url_not_consumed_by_framework_provider_capability",
        }

    if mode == "full-contract-baseline" and "CONTRACT_UNSUPPORTED_SUITE_RUNTIME" in failure_codes:
        return {"framework_consumed": False, "framework_consumption_status": "blocked_before_provider_dispatch"}

    if mode == "full-contract-baseline":
        if dependency.get("provider_type") == "wiremock_http_mock" and dependency.get("provisioner") == "project_docker":
            return {
                "framework_consumed": False,
                "framework_consumption_status": "external_base_url_not_consumed_by_framework_provider_capability",
            }
        provider_ids = _csv_scalar(stdout, "provider_ids")
        provider_id = dependency.get("provider_id")
        consumed = bool(
            runtime_executed
            and framework.get("exit_code") == 0
            and provider_id
            and provider_id in provider_ids
        )
        return {
            "framework_consumed": consumed,
            "framework_consumption_status": "framework_runtime_executed"
            if consumed
            else "framework_runtime_not_confirmed",
        }

    if mode == "jdbc-lightweight" and dependency.get("provisioner") == "framework_embedded_h2":
        consumed = _single_provider_dependency_consumed(stdout, dependency, runtime_executed, framework.get("exit_code"))
        return {
            "framework_consumed": consumed,
            "framework_consumption_status": "framework_runtime_executed"
            if consumed
            else "framework_runtime_not_confirmed",
        }

    if mode == "nats-only" and dependency.get("provider_type") == "nats":
        if "NATS_CONNECTION_FAILED" in failure_codes:
            return {"framework_consumed": False, "framework_consumption_status": "framework_connection_failed"}
        consumed = _single_provider_dependency_consumed(stdout, dependency, runtime_executed, framework.get("exit_code"))
        return {
            "framework_consumed": consumed,
            "framework_consumption_status": "framework_runtime_executed"
            if consumed
            else "framework_runtime_not_confirmed",
        }

    return {"framework_consumed": False, "framework_consumption_status": "framework_runtime_not_confirmed"}


def _single_provider_dependency_consumed(
    stdout: str,
    dependency: dict,
    runtime_executed: bool,
    exit_code: int | None,
) -> bool:
    return bool(
        runtime_executed
        and exit_code == 0
        and _extract_scalar(stdout, "provider_id") == dependency.get("provider_id")
        and _extract_scalar(stdout, "provider_type") == dependency.get("provider_type")
    )


def _csv_scalar(text: str, key: str) -> set[str]:
    value = _extract_scalar(text, key)
    if not value:
        return set()
    return {item.strip() for item in value.split(",") if item.strip()}


if __name__ == "__main__":
    raise SystemExit(main())
