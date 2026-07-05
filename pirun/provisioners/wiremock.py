from __future__ import annotations

import time
import urllib.request
from dataclasses import dataclass

from pirun.docker_cli import DOCKER, build_docker_run_command, remove_by_label, run_command


WIREMOCK_IMAGE = "wiremock/wiremock:3.9.1"


@dataclass
class WireMockProvisionResult:
    provider_id: str
    image: str
    container_id: str
    host: str
    port: int
    base_url: str
    readiness_status: str


def start_wiremock(
    run_id: str,
    *,
    provider_id: str = "wiremock-payment-api",
    suite: str = "wiremock_capability",
) -> WireMockProvisionResult:
    name = f"pirun-{run_id}-wiremock"
    pull = run_command([DOCKER, "pull", WIREMOCK_IMAGE], timeout=300)
    if pull.exit_code != 0:
        raise RuntimeError(f"docker pull failed: {pull.stderr.strip()}")

    cmd = build_docker_run_command(
        run_id=run_id,
        suite=suite,
        name=name,
        image=WIREMOCK_IMAGE,
        ports={"8080/tcp": 0},
        memory="512m",
    )
    result = run_command(cmd, timeout=90)
    if result.exit_code != 0:
        raise RuntimeError(f"docker run failed: {result.stderr.strip()}")

    container_id = result.stdout.strip()
    port_result = run_command([DOCKER, "port", container_id, "8080/tcp"], timeout=30)
    if port_result.exit_code != 0:
        raise RuntimeError(f"docker port failed: {port_result.stderr.strip()}")
    host_port = int(port_result.stdout.strip().rsplit(":", 1)[1])

    base_url = f"http://127.0.0.1:{host_port}"
    wait_for_http(f"{base_url}/__admin", timeout_seconds=30)
    return WireMockProvisionResult(
        provider_id=provider_id,
        image=WIREMOCK_IMAGE,
        container_id=container_id,
        host="127.0.0.1",
        port=host_port,
        base_url=base_url,
        readiness_status="passed",
    )


def wait_for_http(url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if 200 <= response.status < 400:
                    return
        except Exception as exc:
            last_error = exc
            time.sleep(0.5)
    raise TimeoutError(f"WireMock readiness failed for {url}: {last_error}")


def stop_run(run_id: str) -> None:
    result = remove_by_label(run_id)
    if result.exit_code != 0:
        raise RuntimeError(f"docker cleanup failed: {result.stderr.strip()}")
