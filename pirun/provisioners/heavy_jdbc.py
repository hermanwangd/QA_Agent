from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from pirun.docker_cli import build_docker_run_command


BYTES_PER_GIB = 1024 * 1024 * 1024


@dataclass(frozen=True)
class HeavyJdbcEngineConfig:
    engine: str
    mode: str
    provider_id: str
    dialect: str
    suite_dir: str
    container_port: str
    docker_memory_gib: int
    disk_free_gib: int
    container_memory: str
    shm_size: str | None
    startup_timeout_seconds: int
    default_image: str
    service_name: str | None = None
    privileged: bool = False


@dataclass(frozen=True)
class GateResult:
    engine: str
    status: str
    reasons: list[str]
    docker_memory_bytes: int
    disk_free_bytes: int
    required_docker_memory_bytes: int
    required_disk_free_bytes: int


ENGINE_CONFIGS = {
    "oracle": HeavyJdbcEngineConfig(
        engine="oracle",
        mode="jdbc-oracle-container",
        provider_id="oracle-like-db",
        dialect="oracle",
        suite_dir="jdbc_oracle_container",
        container_port="1521/tcp",
        docker_memory_gib=4,
        disk_free_gib=25,
        container_memory="3g",
        shm_size="1g",
        startup_timeout_seconds=600,
        default_image="gvenzl/oracle-free:23-slim-faststart",
        service_name="FREEPDB1",
    ),
    "db2": HeavyJdbcEngineConfig(
        engine="db2",
        mode="jdbc-db2-container",
        provider_id="db2-like-db",
        dialect="db2",
        suite_dir="jdbc_db2_container",
        container_port="50000/tcp",
        docker_memory_gib=8,
        disk_free_gib=40,
        container_memory="6g",
        shm_size=None,
        startup_timeout_seconds=900,
        default_image="icr.io/db2_community/db2",
        privileged=True,
    ),
}


def config_for_engine(engine: str) -> HeavyJdbcEngineConfig:
    if engine not in ENGINE_CONFIGS:
        raise ValueError(f"unsupported heavy JDBC engine: {engine}")
    return ENGINE_CONFIGS[engine]


def evaluate_resource_gate(
    engine: str,
    *,
    env: dict[str, str],
    docker_memory_bytes: int,
    disk_free_bytes: int,
) -> GateResult:
    config = config_for_engine(engine)
    policy_reasons = _policy_reasons(engine, env)
    if policy_reasons:
        return _gate_result(
            config,
            "SKIPPED_POLICY_GATE",
            policy_reasons,
            docker_memory_bytes=docker_memory_bytes,
            disk_free_bytes=disk_free_bytes,
        )

    resource_reasons = []
    if docker_memory_bytes < config.docker_memory_gib * BYTES_PER_GIB:
        resource_reasons.append("docker_memory")
    if disk_free_bytes < config.disk_free_gib * BYTES_PER_GIB:
        resource_reasons.append("disk_free")

    return _gate_result(
        config,
        "SKIPPED_RESOURCE_LIMIT" if resource_reasons else "PASS",
        resource_reasons,
        docker_memory_bytes=docker_memory_bytes,
        disk_free_bytes=disk_free_bytes,
    )


def parse_docker_port(output: str) -> int:
    text = output.strip()
    if not text or ":" not in text:
        raise ValueError(f"cannot parse docker port output: {output!r}")
    return int(text.rsplit(":", 1)[1])


def container_name(run_id: str, engine: str) -> str:
    return f"pirun-{run_id}-{engine}"


def image_for_engine(engine: str, env: dict[str, str] | None = None) -> str:
    config = config_for_engine(engine)
    env = env or {}
    if engine == "oracle":
        return env.get("PIRUN_ORACLE_IMAGE", config.default_image)
    if engine == "db2":
        return env.get("PIRUN_DB2_IMAGE", config.default_image)
    return config.default_image


def build_heavy_jdbc_run_command(
    engine: str,
    *,
    run_id: str,
    image: str,
    password: str,
) -> list[str]:
    config = config_for_engine(engine)
    if engine == "oracle":
        env = {
            "ORACLE_PASSWORD": password,
            "APP_USER": "APP",
            "APP_USER_PASSWORD": password,
        }
    elif engine == "db2":
        env = {
            "LICENSE": "accept",
            "DB2INSTANCE": "db2inst1",
            "DB2INST1_PASSWORD": password,
            "DBNAME": "testdb",
            "BLU": "false",
            "ENABLE_ORACLE_COMPATIBILITY": "false",
            "TO_CREATE_SAMPLEDB": "false",
            "REPODB": "false",
        }
    else:
        raise ValueError(f"unsupported heavy JDBC engine: {engine}")

    return build_docker_run_command(
        run_id=run_id,
        suite=config.suite_dir,
        name=container_name(run_id, engine),
        image=image,
        ports={config.container_port: 0},
        memory=config.container_memory,
        env=env,
        shm_size=config.shm_size,
        privileged=config.privileged,
    )


class HeavyJdbcLock:
    def __init__(self, path: Path):
        self.path = path
        self._fd: int | None = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise RuntimeError(f"heavy JDBC run already in progress: {self.path}") from exc
        os.write(self._fd, str(os.getpid()).encode("utf-8"))

    def release(self) -> None:
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass


def _policy_reasons(engine: str, env: dict[str, str]) -> list[str]:
    reasons = []
    if env.get("PIRUN_ENABLE_HEAVY_DB_CONTAINERS") != "1":
        reasons.append("PIRUN_ENABLE_HEAVY_DB_CONTAINERS")
    if engine == "oracle" and not env.get("PIRUN_ORACLE_IMAGE"):
        reasons.append("PIRUN_ORACLE_IMAGE")
    if engine == "db2":
        if env.get("PIRUN_ACCEPT_DB2_LICENSE") != "1":
            reasons.append("PIRUN_ACCEPT_DB2_LICENSE")
        if env.get("PIRUN_ALLOW_PRIVILEGED_DB2") != "1":
            reasons.append("PIRUN_ALLOW_PRIVILEGED_DB2")
    return reasons


def _gate_result(
    config: HeavyJdbcEngineConfig,
    status: str,
    reasons: list[str],
    *,
    docker_memory_bytes: int,
    disk_free_bytes: int,
) -> GateResult:
    return GateResult(
        engine=config.engine,
        status=status,
        reasons=reasons,
        docker_memory_bytes=docker_memory_bytes,
        disk_free_bytes=disk_free_bytes,
        required_docker_memory_bytes=config.docker_memory_gib * BYTES_PER_GIB,
        required_disk_free_bytes=config.disk_free_gib * BYTES_PER_GIB,
    )
