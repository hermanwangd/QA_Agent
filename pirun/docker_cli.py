from __future__ import annotations

import subprocess
import os
from pathlib import Path
from dataclasses import dataclass


DOCKER = "/usr/local/bin/docker"
DOCKER_DESKTOP_BIN = "/Applications/Docker.app/Contents/Resources/bin"
DOCKER_CONFIG = "/tmp/pirun-docker-config"


@dataclass
class CommandResult:
    exit_code: int
    stdout: str
    stderr: str


def run_command(cmd: list[str], timeout: int = 60) -> CommandResult:
    proc = subprocess.run(
        cmd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=docker_subprocess_env(),
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def docker_subprocess_env() -> dict[str, str]:
    config_dir = Path(DOCKER_CONFIG)
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.json"
    if not config_file.exists():
        config_file.write_text("{}\n", encoding="utf-8")

    env = os.environ.copy()
    existing_path = env.get("PATH", "")
    prefixes = [DOCKER_DESKTOP_BIN, "/usr/local/bin"]
    env["PATH"] = ":".join([*prefixes, existing_path]) if existing_path else ":".join(prefixes)
    env["DOCKER_CONFIG"] = DOCKER_CONFIG
    return env


def build_docker_run_command(
    *,
    run_id: str,
    suite: str,
    name: str,
    image: str,
    ports: dict[str, int],
    memory: str,
    env: dict[str, str] | None = None,
    shm_size: str | None = None,
    privileged: bool = False,
) -> list[str]:
    cmd = [
        DOCKER,
        "run",
        "-d",
        "--name",
        name,
        "--label",
        f"pirun.run_id={run_id}",
        "--label",
        f"pirun.suite={suite}",
        "--memory",
        memory,
    ]
    if shm_size:
        cmd.extend(["--shm-size", shm_size])
    if privileged:
        cmd.append("--privileged")
    for key, value in sorted((env or {}).items()):
        cmd.extend(["--env", f"{key}={value}"])
    for container_port, host_port in sorted(ports.items()):
        port = container_port.split("/", 1)[0]
        host = f"127.0.0.1:{host_port}:{port}" if host_port else f"127.0.0.1::{port}"
        cmd.extend(["-p", host])
    cmd.append(image)
    return cmd


def build_docker_exec_command(container: str, command: list[str]) -> list[str]:
    return [DOCKER, "exec", container, *command]


def docker_port(container: str, container_port: str) -> CommandResult:
    return run_command([DOCKER, "port", container, container_port], timeout=30)


def docker_info_mem_total() -> CommandResult:
    return run_command([DOCKER, "info", "--format", "{{.MemTotal}}"], timeout=30)


def remove_by_label(run_id: str) -> CommandResult:
    list_cmd = [DOCKER, "ps", "-aq", "--filter", f"label=pirun.run_id={run_id}"]
    listed = run_command(list_cmd)
    ids = [line.strip() for line in listed.stdout.splitlines() if line.strip()]
    if not ids:
        return CommandResult(0, "", "")
    return run_command([DOCKER, "rm", "-f", *ids], timeout=60)
