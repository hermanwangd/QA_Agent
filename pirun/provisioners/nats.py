from __future__ import annotations

import socket
import time
from dataclasses import dataclass

from pirun.docker_cli import DOCKER, build_docker_run_command, remove_by_label, run_command


NATS_IMAGE = "nats:2.10-alpine"


@dataclass
class NatsProvisionResult:
    provider_id: str
    image: str
    container_id: str
    host: str
    port: int
    connection_url: str
    readiness_status: str


def start_nats(
    run_id: str,
    *,
    provider_id: str = "local-nats-event-bus",
    suite: str = "nats_capability",
) -> NatsProvisionResult:
    name = f"pirun-{run_id}-nats"
    pull = run_command([DOCKER, "pull", NATS_IMAGE], timeout=300)
    if pull.exit_code != 0:
        raise RuntimeError(f"docker pull failed: {pull.stderr.strip()}")

    cmd = build_docker_run_command(
        run_id=run_id,
        suite=suite,
        name=name,
        image=NATS_IMAGE,
        ports={"4222/tcp": 0},
        memory="256m",
    )
    result = run_command(cmd, timeout=90)
    if result.exit_code != 0:
        raise RuntimeError(f"docker run failed: {result.stderr.strip()}")

    container_id = result.stdout.strip()
    port_result = run_command([DOCKER, "port", container_id, "4222/tcp"], timeout=30)
    if port_result.exit_code != 0:
        raise RuntimeError(f"docker port failed: {port_result.stderr.strip()}")
    host_port = int(port_result.stdout.strip().rsplit(":", 1)[1])

    wait_for_tcp("127.0.0.1", host_port, timeout_seconds=30)
    return NatsProvisionResult(
        provider_id=provider_id,
        image=NATS_IMAGE,
        container_id=container_id,
        host="127.0.0.1",
        port=host_port,
        connection_url=f"nats://127.0.0.1:{host_port}",
        readiness_status="passed",
    )


def wait_for_tcp(host: str, port: int, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error: OSError | None = None
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError as exc:
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"NATS readiness failed for {host}:{port}: {last_error}")


def stop_run(run_id: str) -> None:
    result = remove_by_label(run_id)
    if result.exit_code != 0:
        raise RuntimeError(f"docker cleanup failed: {result.stderr.strip()}")
