from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.docker_cli import (
    CommandResult,
    build_docker_exec_command,
    docker_info_mem_total,
    docker_port,
    remove_by_label,
    run_command,
)
from pirun.framework_paths import DEFAULT_FRAMEWORK_VERSION, framework_paths as resolve_framework_paths
from pirun.materialize.contract_baseline import materialize_heavy_jdbc_container
from pirun.provisioners.heavy_jdbc import (
    GateResult,
    HeavyJdbcLock,
    build_heavy_jdbc_run_command,
    config_for_engine,
    dialect_probe_exec_command,
    evaluate_resource_gate,
    image_for_engine,
    jdbc_connection_url,
    parse_docker_port,
)
from pirun.redaction import redact_text


REPO_ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = REPO_ROOT / ".pirun" / "locks" / "heavy-jdbc-container.lock"


def run_root_for_engine(run_id: str, engine: str) -> Path:
    return REPO_ROOT / ".pirun" / "runs" / run_id / config_for_engine(engine).suite_dir


def docker_memory_bytes() -> int:
    result = docker_info_mem_total()
    if result.exit_code != 0:
        return 0
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def disk_free_bytes() -> int:
    return shutil.disk_usage(REPO_ROOT).free


def classify_result(
    *,
    project_provisioned: bool,
    dialect_probe_passed: bool,
    framework_invoked: bool,
    framework_exit_code: int | None,
    framework_consumed_external_jdbc: bool,
    cleanup_passed: bool,
) -> str:
    if not project_provisioned:
        return "PROJECT_PROVISIONING_FAILED"
    if not dialect_probe_passed:
        return "DIALECT_PROBE_FAILED"
    if not framework_invoked:
        return "FRAMEWORK_NOT_INVOKED"
    if framework_exit_code != 0:
        return "FRAMEWORK_FAILED"
    if not cleanup_passed:
        return "CLEANUP_FAILED"
    if not framework_consumed_external_jdbc:
        return "PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN"
    return "PASS"


def exit_code_for_classification(classification: str) -> int:
    if classification == "PASS" or classification.startswith("SKIPPED_"):
        return 0
    return 1


def framework_consumed_external_jdbc(stdout: str, provider_id: str, exit_code: int | None) -> bool:
    runtime_executed = "provider_runtime_executed: true" in stdout or "provider_runtime_invoked: true" in stdout
    return bool(exit_code == 0 and runtime_executed and f"provider_id: {provider_id}" in stdout)


def wait_for_dialect_probe(
    *,
    engine: str,
    container_id: str,
    password: str,
    timeout_seconds: int,
    interval_seconds: float = 5.0,
    run_command_func: Callable[[list[str], int], CommandResult] = run_command,
    sleep_func: Callable[[float], None] = time.sleep,
) -> dict:
    deadline = time.monotonic() + timeout_seconds
    attempts = 0
    last = CommandResult(1, "", "probe not started")
    while True:
        attempts += 1
        remaining = max(1, int(deadline - time.monotonic()))
        command = build_docker_exec_command(
            container_id,
            dialect_probe_exec_command(engine, password=password),
        )
        last = run_command_func(command, min(60, remaining))
        if last.exit_code == 0 and "1" in last.stdout:
            return {
                "status": "passed",
                "attempts": attempts,
                "stdout": redact_text(last.stdout),
                "stderr": redact_text(last.stderr),
            }
        if time.monotonic() >= deadline:
            return {
                "status": "failed",
                "attempts": attempts,
                "stdout": redact_text(last.stdout),
                "stderr": redact_text(last.stderr),
            }
        sleep_func(interval_seconds)


def write_skip_report(*, run_root: Path, run_id: str, mode: str, gate: GateResult) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    gate_payload = asdict(gate)
    report = {
        "run_id": run_id,
        "mode": mode,
        "db_engine": gate.engine,
        "framework_invoked": False,
        "framework_consumed_external_jdbc": False,
        "cleanup_status": "not_started",
        "result_classification": gate.status,
        "gate": gate_payload,
    }
    (run_root / "resource_gate.yaml").write_text(yaml.safe_dump(gate_payload, sort_keys=False), encoding="utf-8")
    (run_root / "provisioning_evidence.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    (run_root / "dialect_probe.yaml").write_text(
        yaml.safe_dump({"status": "not_started", "reason": gate.status}, sort_keys=False),
        encoding="utf-8",
    )
    (run_root / "cleanup_evidence.yaml").write_text(
        yaml.safe_dump({"cleanup_status": "not_started"}, sort_keys=False),
        encoding="utf-8",
    )
    (run_root / "framework_stdout.txt").write_text("", encoding="utf-8")
    (run_root / "framework_stderr.txt").write_text("", encoding="utf-8")
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def write_run_report(
    *,
    run_root: Path,
    run_id: str,
    mode: str,
    db_engine: str,
    image: str,
    container_id: str | None,
    container_memory: str,
    shm_size: str | None,
    startup_timeout: int,
    startup_duration_seconds: float | None,
    host_port: int | None,
    dialect_probe: dict,
    framework_invoked: bool,
    framework_exit_code: int | None,
    framework_stdout: str,
    framework_stderr: str,
    framework_consumed_external_jdbc: bool,
    cleanup_status: str,
    result_classification: str,
    gate: GateResult,
) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    gate_payload = asdict(gate)
    safe_probe = {
        **dialect_probe,
        "stdout": redact_text(str(dialect_probe.get("stdout", ""))),
        "stderr": redact_text(str(dialect_probe.get("stderr", ""))),
    }
    report = {
        "run_id": run_id,
        "mode": mode,
        "db_engine": db_engine,
        "image": image,
        "container_id": container_id,
        "container_memory": container_memory,
        "shm_size": shm_size,
        "startup_timeout": startup_timeout,
        "startup_duration_seconds": startup_duration_seconds,
        "host_port": host_port,
        "dialect_probe_status": safe_probe.get("status"),
        "framework_invoked": framework_invoked,
        "framework_exit_code": framework_exit_code,
        "framework_consumed_external_jdbc": framework_consumed_external_jdbc,
        "cleanup_status": cleanup_status,
        "result_classification": result_classification,
        "gate": gate_payload,
    }
    (run_root / "resource_gate.yaml").write_text(yaml.safe_dump(gate_payload, sort_keys=False), encoding="utf-8")
    (run_root / "provisioning_evidence.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    (run_root / "dialect_probe.yaml").write_text(yaml.safe_dump(safe_probe, sort_keys=False), encoding="utf-8")
    (run_root / "cleanup_evidence.yaml").write_text(
        yaml.safe_dump({"cleanup_status": cleanup_status, "container_id": container_id}, sort_keys=False),
        encoding="utf-8",
    )
    (run_root / "framework_stdout.txt").write_text(redact_text(framework_stdout), encoding="utf-8")
    (run_root / "framework_stderr.txt").write_text(redact_text(framework_stderr), encoding="utf-8")
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", choices=["oracle", "db2"], required=True)
    parser.add_argument("--profile", default="ci")
    parser.add_argument("--run-id", default=f"PIRUN-HEAVY-{int(time.time())}")
    parser.add_argument("--framework-version", default=DEFAULT_FRAMEWORK_VERSION)
    args = parser.parse_args()

    config = config_for_engine(args.db)
    run_root = run_root_for_engine(args.run_id, args.db)
    env = os.environ.copy()
    gate = evaluate_resource_gate(
        args.db,
        env=env,
        docker_memory_bytes=docker_memory_bytes(),
        disk_free_bytes=disk_free_bytes(),
    )
    if gate.status != "PASS":
        write_skip_report(run_root=run_root, run_id=args.run_id, mode=config.mode, gate=gate)
        return 0

    lock = HeavyJdbcLock(LOCK_PATH)
    password = env.get("PIRUN_HEAVY_JDBC_PASSWORD") or secrets.token_urlsafe(18)
    image = image_for_engine(args.db, env)
    container_id = None
    host_port = None
    dialect_probe = {"status": "not_started", "attempts": 0, "stdout": "", "stderr": ""}
    framework_invoked = False
    framework_exit_code = None
    framework_stdout = ""
    framework_stderr = ""
    cleanup_status = "not_started"
    project_provisioned = False
    startup_duration_seconds = None

    try:
        lock.acquire()
        started_at = time.monotonic()
        run_cmd = build_heavy_jdbc_run_command(args.db, run_id=args.run_id, image=image, password=password)
        run_result = run_command(run_cmd, timeout=60)
        if run_result.exit_code != 0:
            raise RuntimeError(run_result.stderr.strip())
        container_id = run_result.stdout.strip()

        port_result = docker_port(container_id, config.container_port)
        if port_result.exit_code != 0:
            raise RuntimeError(port_result.stderr.strip())
        host_port = parse_docker_port(port_result.stdout)

        dialect_probe = wait_for_dialect_probe(
            engine=args.db,
            container_id=container_id,
            password=password,
            timeout_seconds=config.startup_timeout_seconds,
        )
        startup_duration_seconds = round(time.monotonic() - started_at, 3)
        project_provisioned = dialect_probe["status"] == "passed"

        materialize_heavy_jdbc_container(
            run_dir=run_root,
            provider_id=config.provider_id,
            dialect=config.dialect,
            connection_secret_ref="env://JDBC_CONNECTION",
            profile=args.profile,
        )

        if project_provisioned:
            paths = resolve_framework_paths(args.framework_version, repo_root=REPO_ROOT)
            framework_env = env.copy()
            framework_env["JDBC_CONNECTION"] = jdbc_connection_url(
                args.db,
                host_port,
                service_name=config.service_name,
            )
            proc = subprocess.run(
                [
                    "java",
                    "-Xmx512m",
                    "-jar",
                    str(paths.jar),
                    "run",
                    "--suite",
                    str(run_root / "suite_manifest.yaml"),
                    "--profile",
                    args.profile,
                ],
                cwd=str(paths.usage_kit_root),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=framework_env,
                timeout=180,
            )
            framework_invoked = True
            framework_exit_code = proc.returncode
            framework_stdout = proc.stdout
            framework_stderr = proc.stderr
    except Exception as exc:
        framework_stderr = f"{framework_stderr}\nrunner_error: {exc}".strip()
    finally:
        cleanup = remove_by_label(args.run_id)
        cleanup_status = "passed" if cleanup.exit_code == 0 else "failed"
        lock.release()

    consumed = framework_consumed_external_jdbc(framework_stdout, config.provider_id, framework_exit_code)
    classification = classify_result(
        project_provisioned=project_provisioned,
        dialect_probe_passed=dialect_probe.get("status") == "passed",
        framework_invoked=framework_invoked,
        framework_exit_code=framework_exit_code,
        framework_consumed_external_jdbc=consumed,
        cleanup_passed=cleanup_status == "passed",
    )
    write_run_report(
        run_root=run_root,
        run_id=args.run_id,
        mode=config.mode,
        db_engine=args.db,
        image=image,
        container_id=container_id,
        container_memory=config.container_memory,
        shm_size=config.shm_size,
        startup_timeout=config.startup_timeout_seconds,
        startup_duration_seconds=startup_duration_seconds,
        host_port=host_port,
        dialect_probe=dialect_probe,
        framework_invoked=framework_invoked,
        framework_exit_code=framework_exit_code,
        framework_stdout=framework_stdout,
        framework_stderr=framework_stderr,
        framework_consumed_external_jdbc=consumed,
        cleanup_status=cleanup_status,
        result_classification=classification,
        gate=gate,
    )
    return exit_code_for_classification(classification)


if __name__ == "__main__":
    raise SystemExit(main())
