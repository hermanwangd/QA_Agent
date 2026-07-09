# Heavy JDBC Container PI-run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in project-side Oracle and DB2 JDBC container PI-runs that produce provisioning, dialect, framework-consumption, and cleanup evidence without adding heavy database provisioning to the released framework jar.

**Architecture:** Keep heavy database lifecycle ownership in the PI-run project. The runner gates resources and policy first, starts exactly one heavy DB container through the existing Docker CLI style, materializes an external-JDBC suite using `env://PIRUN_JDBC_CONNECTION`, invokes the released framework jar with bounded JVM memory, classifies framework consumption separately from project provisioning, and always cleans up by PI-run labels.

**Tech Stack:** Python 3 stdlib, `unittest`, PyYAML, Docker CLI, released `spec-driven-auto-regression-*.jar`, Oracle/DB2 container-native SQL clients through `docker exec`.

---

## Execution Rules

- Do not run Oracle and DB2 together.
- Do not start any heavy DB container unless `PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1`.
- Do not run DB2 locally by default; require `PIRUN_ACCEPT_DB2_LICENSE=1` and `PIRUN_ALLOW_PRIVILEGED_DB2=1`.
- Keep framework invocation bounded with `java -Xmx512m`.
- Unit tests must not require Docker or network access.
- A skipped resource or policy gate writes evidence and exits `0`.
- A failed container startup, failed dialect probe, failed framework invocation, or failed cleanup writes evidence and exits non-zero.

## File Structure

- Modify: `pirun/docker_cli.py`
  - Add Docker command options needed by heavy DBs: `--env`, `--shm-size`, `--privileged`, dynamic port inspection, `docker exec`.
- Create: `pirun/provisioners/heavy_jdbc.py`
  - Own resource gates, policy gates, lock handling, engine config, container command construction, readiness/dialect probe commands, and result dataclasses.
- Modify: `pirun/materialize/contract_baseline.py`
  - Add `materialize_heavy_jdbc_container()` so heavy JDBC uses the existing usage-kit JDBC sample but replaces generated H2 refs with `env://PIRUN_JDBC_CONNECTION`.
- Create: `pirun/run_heavy_jdbc_container.py`
  - CLI orchestrator for `--db oracle|db2`; writes all evidence files under `.pirun/runs/<run_id>/jdbc_<db>_container/`.
- Create: `tests/test_pirun_heavy_jdbc_gates.py`
  - Gate, lock, classification, and command-construction tests.
- Create: `tests/test_pirun_heavy_jdbc_materialize.py`
  - Suite materialization tests proving no generated H2 refs remain.
- Create: `tests/test_pirun_heavy_jdbc_runner.py`
  - Runner tests using patched provisioner/framework calls; no real Docker.
- Modify: `README.md`
  - Add the heavy JDBC commands and clarify that real Oracle/DB2 runs are manual opt-in.

## Task 1: Extend Docker CLI Primitives

**Files:**
- Modify: `pirun/docker_cli.py`
- Modify: `tests/test_pirun_docker_cli.py`

- [ ] **Step 1: Add failing tests for heavy DB Docker options**

Append these tests to `tests/test_pirun_docker_cli.py`:

```python
    def test_build_run_command_supports_env_shm_and_privileged(self):
        cmd = build_docker_run_command(
            run_id="RUN-HEAVY",
            suite="jdbc_oracle_container",
            name="pirun-RUN-HEAVY-oracle",
            image="gvenzl/oracle-free:23-slim-faststart",
            ports={"1521/tcp": 0},
            memory="3g",
            env={"ORACLE_PASSWORD": "Secret-12345", "APP_USER": "APP", "APP_USER_PASSWORD": "Secret-12345"},
            shm_size="1g",
            privileged=False,
        )

        joined = " ".join(cmd)
        self.assertIn("--shm-size", cmd)
        self.assertIn("1g", cmd)
        self.assertIn("--env", cmd)
        self.assertIn("ORACLE_PASSWORD=Secret-12345", cmd)
        self.assertIn("APP_USER=APP", cmd)
        self.assertIn("APP_USER_PASSWORD=Secret-12345", cmd)
        self.assertNotIn("--privileged", cmd)
        self.assertIn("127.0.0.1::1521", joined)

    def test_build_run_command_supports_db2_privileged_mode(self):
        cmd = build_docker_run_command(
            run_id="RUN-DB2",
            suite="jdbc_db2_container",
            name="pirun-RUN-DB2-db2",
            image="icr.io/db2_community/db2",
            ports={"50000/tcp": 0},
            memory="6g",
            env={"LICENSE": "accept", "DB2INSTANCE": "db2inst1", "DBNAME": "testdb"},
            privileged=True,
        )

        self.assertIn("--privileged", cmd)
        self.assertIn("--env", cmd)
        self.assertIn("LICENSE=accept", cmd)
        self.assertIn("DB2INSTANCE=db2inst1", cmd)
        self.assertIn("DBNAME=testdb", cmd)

    def test_docker_exec_command_uses_configured_binary(self):
        cmd = build_docker_exec_command("pirun-RUN-db", ["bash", "-lc", "echo ok"])

        self.assertEqual(cmd[:3], ["/usr/local/bin/docker", "exec", "pirun-RUN-db"])
        self.assertEqual(cmd[3:], ["bash", "-lc", "echo ok"])
```

- [ ] **Step 2: Run the targeted tests and verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_docker_cli
```

Expected result before implementation:

```text
FAILED
NameError: name 'build_docker_exec_command' is not defined
```

- [ ] **Step 3: Implement Docker CLI options**

Change `build_docker_run_command()` in `pirun/docker_cli.py` to this signature and body:

```python
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
```

Add these helpers below `build_docker_run_command()`:

```python
def build_docker_exec_command(container: str, command: list[str]) -> list[str]:
    return [DOCKER, "exec", container, *command]


def docker_port(container: str, container_port: str) -> CommandResult:
    return run_command([DOCKER, "port", container, container_port], timeout=30)


def docker_info_mem_total() -> CommandResult:
    return run_command([DOCKER, "info", "--format", "{{.MemTotal}}"], timeout=30)
```

- [ ] **Step 4: Run Docker CLI tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_docker_cli
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git add pirun/docker_cli.py tests/test_pirun_docker_cli.py
git commit -m "feat: extend pirun docker cli options"
```

## Task 2: Add Heavy JDBC Gate Model

**Files:**
- Create: `pirun/provisioners/heavy_jdbc.py`
- Create: `tests/test_pirun_heavy_jdbc_gates.py`

- [ ] **Step 1: Add failing tests for policy and resource gates**

Create `tests/test_pirun_heavy_jdbc_gates.py`:

```python
import os
import tempfile
import unittest
from pathlib import Path

from pirun.provisioners.heavy_jdbc import (
    BYTES_PER_GIB,
    HeavyJdbcLock,
    evaluate_resource_gate,
    parse_docker_port,
)


class HeavyJdbcGateTests(unittest.TestCase):
    def test_oracle_requires_global_opt_in(self):
        result = evaluate_resource_gate(
            "oracle",
            env={},
            docker_memory_bytes=8 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_POLICY_GATE")
        self.assertIn("PIRUN_ENABLE_HEAVY_DB_CONTAINERS", result.reasons)

    def test_oracle_passes_with_opt_in_and_resources(self):
        result = evaluate_resource_gate(
            "oracle",
            env={
                "PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1",
                "PIRUN_ORACLE_IMAGE": "gvenzl/oracle-free:23-slim-faststart",
            },
            docker_memory_bytes=8 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "PASS")

    def test_db2_requires_license_and_privileged_gates(self):
        result = evaluate_resource_gate(
            "db2",
            env={"PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1"},
            docker_memory_bytes=16 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_POLICY_GATE")
        self.assertIn("PIRUN_ACCEPT_DB2_LICENSE", result.reasons)
        self.assertIn("PIRUN_ALLOW_PRIVILEGED_DB2", result.reasons)

    def test_db2_skips_when_docker_memory_is_too_low(self):
        result = evaluate_resource_gate(
            "db2",
            env={
                "PIRUN_ENABLE_HEAVY_DB_CONTAINERS": "1",
                "PIRUN_ACCEPT_DB2_LICENSE": "1",
                "PIRUN_ALLOW_PRIVILEGED_DB2": "1",
            },
            docker_memory_bytes=4 * BYTES_PER_GIB,
            disk_free_bytes=80 * BYTES_PER_GIB,
        )

        self.assertEqual(result.status, "SKIPPED_RESOURCE_LIMIT")
        self.assertIn("docker_memory", result.reasons)

    def test_parse_docker_port_accepts_ipv4_output(self):
        self.assertEqual(parse_docker_port("127.0.0.1:51521\n"), 51521)

    def test_lock_prevents_parallel_heavy_db_runs(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock_path = Path(tmp) / "heavy-jdbc-container.lock"
            first = HeavyJdbcLock(lock_path)
            first.acquire()
            second = HeavyJdbcLock(lock_path)
            with self.assertRaises(RuntimeError):
                second.acquire()
            first.release()
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the targeted tests and verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_gates
```

Expected before implementation:

```text
FAILED
ModuleNotFoundError: No module named 'pirun.provisioners.heavy_jdbc'
```

- [ ] **Step 3: Implement gate dataclasses and lock**

Create `pirun/provisioners/heavy_jdbc.py`:

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


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
    reasons: list[str] = []
    if env.get("PIRUN_ENABLE_HEAVY_DB_CONTAINERS") != "1":
        reasons.append("PIRUN_ENABLE_HEAVY_DB_CONTAINERS")
    if engine == "oracle" and not env.get("PIRUN_ORACLE_IMAGE"):
        reasons.append("PIRUN_ORACLE_IMAGE")
    if engine == "db2":
        if env.get("PIRUN_ACCEPT_DB2_LICENSE") != "1":
            reasons.append("PIRUN_ACCEPT_DB2_LICENSE")
        if env.get("PIRUN_ALLOW_PRIVILEGED_DB2") != "1":
            reasons.append("PIRUN_ALLOW_PRIVILEGED_DB2")
    if reasons:
        return GateResult(
            engine=engine,
            status="SKIPPED_POLICY_GATE",
            reasons=reasons,
            docker_memory_bytes=docker_memory_bytes,
            disk_free_bytes=disk_free_bytes,
            required_docker_memory_bytes=config.docker_memory_gib * BYTES_PER_GIB,
            required_disk_free_bytes=config.disk_free_gib * BYTES_PER_GIB,
        )

    resource_reasons: list[str] = []
    if docker_memory_bytes < config.docker_memory_gib * BYTES_PER_GIB:
        resource_reasons.append("docker_memory")
    if disk_free_bytes < config.disk_free_gib * BYTES_PER_GIB:
        resource_reasons.append("disk_free")
    status = "SKIPPED_RESOURCE_LIMIT" if resource_reasons else "PASS"
    return GateResult(
        engine=engine,
        status=status,
        reasons=resource_reasons,
        docker_memory_bytes=docker_memory_bytes,
        disk_free_bytes=disk_free_bytes,
        required_docker_memory_bytes=config.docker_memory_gib * BYTES_PER_GIB,
        required_disk_free_bytes=config.disk_free_gib * BYTES_PER_GIB,
    )


def parse_docker_port(output: str) -> int:
    text = output.strip()
    if not text or ":" not in text:
        raise ValueError(f"cannot parse docker port output: {output!r}")
    return int(text.rsplit(":", 1)[1])


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
```

- [ ] **Step 4: Run gate tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_gates
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git add pirun/provisioners/heavy_jdbc.py tests/test_pirun_heavy_jdbc_gates.py
git commit -m "feat: add heavy jdbc gate model"
```

## Task 3: Build Heavy JDBC Container Commands

**Files:**
- Modify: `pirun/provisioners/heavy_jdbc.py`
- Modify: `tests/test_pirun_heavy_jdbc_gates.py`

- [ ] **Step 1: Add failing tests for Oracle and DB2 command construction**

Append these tests to `HeavyJdbcGateTests`:

```python
    def test_oracle_run_command_uses_faststart_image_shm_and_app_user(self):
        command = build_heavy_jdbc_run_command(
            "oracle",
            run_id="RUN-ORACLE",
            image="gvenzl/oracle-free:23-slim-faststart",
            password="Secret-12345",
        )
        joined = " ".join(command)

        self.assertIn("--memory 3g", joined)
        self.assertIn("--shm-size 1g", joined)
        self.assertIn("ORACLE_PASSWORD=Secret-12345", joined)
        self.assertIn("APP_USER=APP", joined)
        self.assertIn("APP_USER_PASSWORD=Secret-12345", joined)
        self.assertIn("gvenzl/oracle-free:23-slim-faststart", joined)
        self.assertNotIn("--privileged", command)

    def test_db2_run_command_requires_privileged_license_and_password(self):
        command = build_heavy_jdbc_run_command(
            "db2",
            run_id="RUN-DB2",
            image="icr.io/db2_community/db2",
            password="Secret-12345",
        )
        joined = " ".join(command)

        self.assertIn("--privileged", command)
        self.assertIn("--memory 6g", joined)
        self.assertIn("LICENSE=accept", joined)
        self.assertIn("DB2INSTANCE=db2inst1", joined)
        self.assertIn("DB2INST1_PASSWORD=Secret-12345", joined)
        self.assertIn("DBNAME=testdb", joined)
        self.assertIn("icr.io/db2_community/db2", joined)
```

Also update the import block:

```python
from pirun.provisioners.heavy_jdbc import (
    BYTES_PER_GIB,
    HeavyJdbcLock,
    build_heavy_jdbc_run_command,
    evaluate_resource_gate,
    parse_docker_port,
)
```

- [ ] **Step 2: Run the targeted tests and verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_gates
```

Expected before implementation:

```text
FAILED
ImportError: cannot import name 'build_heavy_jdbc_run_command'
```

- [ ] **Step 3: Implement command construction**

Add this import to `pirun/provisioners/heavy_jdbc.py`:

```python
from pirun.docker_cli import build_docker_run_command
```

Add these functions:

```python
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
```

- [ ] **Step 4: Run command construction tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_gates
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git add pirun/provisioners/heavy_jdbc.py tests/test_pirun_heavy_jdbc_gates.py
git commit -m "feat: build heavy jdbc container commands"
```

## Task 4: Materialize External JDBC Suites

**Files:**
- Modify: `pirun/materialize/contract_baseline.py`
- Create: `tests/test_pirun_heavy_jdbc_materialize.py`

- [ ] **Step 1: Add failing materialization tests**

Create `tests/test_pirun_heavy_jdbc_materialize.py`:

```python
import tempfile
import unittest
from pathlib import Path

import yaml

from pirun.materialize.contract_baseline import materialize_heavy_jdbc_container


class HeavyJdbcMaterializeTests(unittest.TestCase):
    def test_materialize_oracle_external_jdbc_uses_env_binding_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_oracle_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="oracle-like-db",
                dialect="oracle",
                connection_secret_ref="env://PIRUN_JDBC_CONNECTION",
                profile="ci",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            execution_profile = run_dir / "execution_profiles" / "ci.yaml"
            test_case = run_dir / "test_case.yaml"
            project_binding = run_dir / "project_bindings" / "oracle-like-db.yaml"

            combined = "\n".join(p.read_text() for p in [env_binding, env_profile, execution_profile, test_case])
            self.assertIn("env://PIRUN_JDBC_CONNECTION", combined)
            self.assertIn("dialect: oracle", combined)
            self.assertIn("allowed_provisioners:\n  - project_docker", combined)
            self.assertIn("project_provisioned_dependency: docker_jdbc_oracle", combined)
            self.assertNotIn("generated://", combined)
            self.assertTrue(project_binding.exists())

    def test_materialize_db2_external_jdbc_uses_db2_provider(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "jdbc_db2_container"
            materialize_heavy_jdbc_container(
                run_dir=run_dir,
                provider_id="db2-like-db",
                dialect="db2",
                connection_secret_ref="env://PIRUN_JDBC_CONNECTION",
                profile="ci",
            )

            env_binding = yaml.safe_load((run_dir / "environment_bindings" / "ci.yaml").read_text())
            provider_binding = env_binding["provider_bindings"][0]

            self.assertEqual(provider_binding["provider_id"], "db2-like-db")
            self.assertEqual(provider_binding["binding_values"]["dialect"], "db2")
            self.assertEqual(provider_binding["binding_values"]["connection"]["secret_ref"], "env://PIRUN_JDBC_CONNECTION")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run materialization tests and verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_materialize
```

Expected before implementation:

```text
FAILED
ImportError: cannot import name 'materialize_heavy_jdbc_container'
```

- [ ] **Step 3: Implement materializer**

Add this function to `pirun/materialize/contract_baseline.py` after `materialize_jdbc_lightweight()`:

```python
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
    provider_instance_path = run_dir / "provider_instances" / "oracle_like.yaml"

    _write_suite_policy(
        suite_path,
        profile=profile,
        purpose=f"Project-provisioned Docker {dialect.upper()} JDBC capability verification.",
    )
    _write_test_labels(test_case_path, profile=profile, dependency=f"docker_jdbc_{dialect}")
    if provider_instance_path.exists():
        _write_provider_labels(provider_instance_path)

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = f"{profile}-project-docker-jdbc-{dialect}"
    env_binding["profile"] = profile
    env_binding["provider_bindings"] = [
        {
            "provider_id": provider_id,
            "provider_instance_ref": "provider_instances/oracle_like.yaml",
            "runtime_mode": "external",
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
    env_profile["dependency_substitution_policy"] = {"allowed_runtime_modes": ["external"]}
    env_profile["dependency_provisioning_policy"] = {
        "allowed_provisioners": ["project_docker"],
        "startup_policy": "project_before_framework",
        "readiness_policy": "project_sql_probe",
        "cleanup_scope": "project_finally",
    }
    env_profile["providers"] = {
        provider_id: {
            "runtime_mode": "external",
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
        "readiness_policy": "sql_probe",
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
```

- [ ] **Step 4: Run materialization tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_materialize tests.test_pirun_materialize
```

Expected:

```text
OK
```

- [ ] **Step 5: Commit**

```bash
git add pirun/materialize/contract_baseline.py tests/test_pirun_heavy_jdbc_materialize.py
git commit -m "feat: materialize external jdbc container suites"
```

## Task 5: Add Heavy JDBC Orchestrator

**Files:**
- Create: `pirun/run_heavy_jdbc_container.py`
- Modify: `pirun/provisioners/heavy_jdbc.py`
- Create: `tests/test_pirun_heavy_jdbc_runner.py`

- [ ] **Step 1: Add failing runner tests**

Create `tests/test_pirun_heavy_jdbc_runner.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pirun.provisioners.heavy_jdbc import GateResult, BYTES_PER_GIB
from pirun.run_heavy_jdbc_container import classify_result, write_skip_report


class HeavyJdbcRunnerTests(unittest.TestCase):
    def test_skip_report_writes_resource_gate_and_project_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_root = Path(tmp) / "jdbc_oracle_container"
            gate = GateResult(
                engine="oracle",
                status="SKIPPED_RESOURCE_LIMIT",
                reasons=["docker_memory"],
                docker_memory_bytes=2 * BYTES_PER_GIB,
                disk_free_bytes=80 * BYTES_PER_GIB,
                required_docker_memory_bytes=4 * BYTES_PER_GIB,
                required_disk_free_bytes=25 * BYTES_PER_GIB,
            )

            write_skip_report(
                run_root=run_root,
                run_id="RUN-SKIP",
                mode="jdbc-oracle-container",
                gate=gate,
            )

            self.assertTrue((run_root / "resource_gate.yaml").exists())
            report = json.loads((run_root / "project_report.json").read_text())
            self.assertEqual(report["result_classification"], "SKIPPED_RESOURCE_LIMIT")
            self.assertFalse(report["framework_invoked"])

    def test_classify_result_requires_framework_consumption_for_full_pass(self):
        self.assertEqual(
            classify_result(
                project_provisioned=True,
                dialect_probe_passed=True,
                framework_invoked=True,
                framework_exit_code=0,
                framework_consumed_external_jdbc=False,
                cleanup_passed=True,
            ),
            "PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN",
        )
        self.assertEqual(
            classify_result(
                project_provisioned=True,
                dialect_probe_passed=True,
                framework_invoked=True,
                framework_exit_code=0,
                framework_consumed_external_jdbc=True,
                cleanup_passed=True,
            ),
            "PASS",
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run runner tests and verify failure**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_runner
```

Expected before implementation:

```text
FAILED
ModuleNotFoundError: No module named 'pirun.run_heavy_jdbc_container'
```

- [ ] **Step 3: Add dialect probe command builders**

Append these functions to `pirun/provisioners/heavy_jdbc.py`:

```python
def jdbc_connection_url(engine: str, host_port: int, *, service_name: str | None = None) -> str:
    if engine == "oracle":
        service = service_name or config_for_engine("oracle").service_name or "FREEPDB1"
        return f"jdbc:oracle:thin:@//127.0.0.1:{host_port}/{service}"
    if engine == "db2":
        return f"jdbc:db2://127.0.0.1:{host_port}/testdb"
    raise ValueError(f"unsupported heavy JDBC engine: {engine}")


def dialect_probe_exec_command(engine: str, *, container: str, password: str) -> list[str]:
    if engine == "oracle":
        sql = (
            "printf 'set heading off feedback off\\n"
            "select 1 from dual;\\n"
            "exit\\n' | sqlplus -L -S APP/"
            f"{password}@localhost/FREEPDB1"
        )
        return ["bash", "-lc", sql]
    if engine == "db2":
        sql = (
            "su - db2inst1 -c \""
            f"db2 connect to testdb user db2inst1 using {password} >/dev/null && "
            "db2 -x 'select 1 from sysibm.sysdummy1'\""
        )
        return ["bash", "-lc", sql]
    raise ValueError(f"unsupported heavy JDBC engine: {engine}")
```

- [ ] **Step 4: Implement runner report helpers**

Create `pirun/run_heavy_jdbc_container.py`:

```python
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

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.docker_cli import build_docker_exec_command, docker_info_mem_total, docker_port, remove_by_label, run_command
from pirun.framework_paths import DEFAULT_FRAMEWORK_VERSION, framework_paths as resolve_framework_paths
from pirun.materialize.contract_baseline import materialize_heavy_jdbc_container
from pirun.provisioners.heavy_jdbc import (
    BYTES_PER_GIB,
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
    if not framework_consumed_external_jdbc:
        return "PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN"
    if not cleanup_passed:
        return "CLEANUP_FAILED"
    return "PASS"


def write_skip_report(*, run_root: Path, run_id: str, mode: str, gate: GateResult) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    gate_payload = asdict(gate)
    (run_root / "resource_gate.yaml").write_text(yaml.safe_dump(gate_payload, sort_keys=False), encoding="utf-8")
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
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


def framework_consumed_external_jdbc(stdout: str, provider_id: str, exit_code: int | None) -> bool:
    return bool(
        exit_code == 0
        and "provider_runtime_executed: true" in stdout
        and f"provider_id: {provider_id}" in stdout
    )
```

- [ ] **Step 5: Run runner helper tests**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_runner
```

Expected:

```text
OK
```

- [ ] **Step 6: Add CLI orchestration**

Append this to `pirun/run_heavy_jdbc_container.py`:

```python
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
    dialect_probe_status = "not_started"
    framework_invoked = False
    framework_exit_code = None
    framework_stdout = ""
    framework_stderr = ""
    cleanup_status = "not_started"
    project_provisioned = False

    try:
        lock.acquire()
        run_cmd = build_heavy_jdbc_run_command(args.db, run_id=args.run_id, image=image, password=password)
        run_result = run_command(run_cmd, timeout=60)
        if run_result.exit_code != 0:
            raise RuntimeError(run_result.stderr.strip())
        container_id = run_result.stdout.strip()

        port_result = docker_port(container_id, config.container_port)
        if port_result.exit_code != 0:
            raise RuntimeError(port_result.stderr.strip())
        host_port = parse_docker_port(port_result.stdout)
        connection_url = jdbc_connection_url(args.db, host_port, service_name=config.service_name)

        probe_cmd = build_docker_exec_command(
            container_id,
            dialect_probe_exec_command(args.db, container=container_id, password=password),
        )
        probe_result = run_command(probe_cmd, timeout=config.startup_timeout_seconds)
        dialect_probe_status = "passed" if probe_result.exit_code == 0 and "1" in probe_result.stdout else "failed"
        project_provisioned = dialect_probe_status == "passed"

        materialize_heavy_jdbc_container(
            run_dir=run_root,
            provider_id=config.provider_id,
            dialect=config.dialect,
            connection_secret_ref="env://PIRUN_JDBC_CONNECTION",
            profile=args.profile,
        )

        paths = resolve_framework_paths(args.framework_version, repo_root=REPO_ROOT)
        framework_env = env.copy()
        framework_env["PIRUN_JDBC_CONNECTION"] = connection_url
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
        dialect_probe_passed=dialect_probe_status == "passed",
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
        host_port=host_port,
        dialect_probe_status=dialect_probe_status,
        framework_invoked=framework_invoked,
        framework_exit_code=framework_exit_code,
        framework_stdout=framework_stdout,
        framework_stderr=framework_stderr,
        framework_consumed_external_jdbc=consumed,
        cleanup_status=cleanup_status,
        result_classification=classification,
        gate=gate,
    )
    return 0 if classification == "PASS" or classification.startswith("SKIPPED_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

Add `write_run_report()` above `main()`:

```python
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
    host_port: int | None,
    dialect_probe_status: str,
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
    dialect_probe = {
        "db_engine": db_engine,
        "dialect_probe_status": dialect_probe_status,
        "host_port": host_port,
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
        "host_port": host_port,
        "dialect_probe_status": dialect_probe_status,
        "framework_invoked": framework_invoked,
        "framework_exit_code": framework_exit_code,
        "framework_consumed_external_jdbc": framework_consumed_external_jdbc,
        "cleanup_status": cleanup_status,
        "result_classification": result_classification,
        "gate": gate_payload,
    }
    (run_root / "resource_gate.yaml").write_text(yaml.safe_dump(gate_payload, sort_keys=False), encoding="utf-8")
    (run_root / "provisioning_evidence.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    (run_root / "dialect_probe.yaml").write_text(yaml.safe_dump(dialect_probe, sort_keys=False), encoding="utf-8")
    (run_root / "cleanup_evidence.yaml").write_text(
        yaml.safe_dump({"cleanup_status": cleanup_status, "container_id": container_id}, sort_keys=False),
        encoding="utf-8",
    )
    (run_root / "framework_stdout.txt").write_text(redact_text(framework_stdout), encoding="utf-8")
    (run_root / "framework_stderr.txt").write_text(redact_text(framework_stderr), encoding="utf-8")
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
```

- [ ] **Step 7: Run runner tests and full lightweight suite**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests.test_pirun_heavy_jdbc_runner tests.test_pirun_heavy_jdbc_gates
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

Expected:

```text
OK
```

- [ ] **Step 8: Commit**

```bash
git add pirun/run_heavy_jdbc_container.py pirun/provisioners/heavy_jdbc.py tests/test_pirun_heavy_jdbc_runner.py
git commit -m "feat: add heavy jdbc container runner"
```

## Task 6: Add Documentation and Manual Verification Commands

**Files:**
- Modify: `README.md`
- Modify: `reports/pi-run-heavy-jdbc-container-proposal.md`

- [ ] **Step 1: Add README command section**

Append this section to `README.md`:

````markdown
## Heavy JDBC Container PI-run

Oracle and DB2 container runs are manual opt-in checks. They are not part of the default unit test suite or `full-contract-baseline`.

Oracle:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ORACLE_IMAGE=gvenzl/oracle-free:23-slim-faststart \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db oracle --framework-version 0.2.5
```

DB2:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ACCEPT_DB2_LICENSE=1 \
PIRUN_ALLOW_PRIVILEGED_DB2=1 \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db db2 --framework-version 0.2.5
```

On an 8 GB local machine, run only Oracle after Docker has at least 4 GB available. Run DB2 on a dedicated CI runner with at least 16 GB host RAM and Docker memory configured to 8 GB or more.
````

- [ ] **Step 2: Add implemented-file section to proposal**

Append this to `reports/pi-run-heavy-jdbc-container-proposal.md`:

````markdown
## Implementation Plan

The implementation plan is tracked in:

```text
docs/superpowers/plans/2026-07-09-heavy-jdbc-container-pirun.md
```
````

- [ ] **Step 3: Run documentation and whitespace checks**

Run:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

Expected:

```text
OK
```

- [ ] **Step 4: Commit**

```bash
git add README.md reports/pi-run-heavy-jdbc-container-proposal.md
git commit -m "docs: document heavy jdbc container runs"
```

## Task 7: Manual Oracle Verification

**Files:**
- Runtime output: `.pirun/runs/<run_id>/jdbc_oracle_container/`
- Report output: `.pirun/runs/<run_id>/jdbc_oracle_container/project_report.json`

- [ ] **Step 1: Check Docker availability without starting Oracle**

Run:

```bash
/usr/local/bin/docker info --format '{{.MemTotal}}'
df -g .
```

Expected:

```text
Docker memory is at least 4294967296 bytes.
Free disk is at least 25 GiB.
```

- [ ] **Step 2: Run Oracle only**

Run:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ORACLE_IMAGE=gvenzl/oracle-free:23-slim-faststart \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db oracle --framework-version 0.2.5
```

Expected:

```text
Exit code 0 only when project_report.json result_classification is PASS.
If result_classification is PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN, exit code is non-zero because framework JDBC provider consumption was not proven.
dialect_probe.yaml dialect_probe_status is passed.
cleanup_evidence.yaml cleanup_status is passed.
```

- [ ] **Step 3: Confirm no Oracle container remains**

Run:

```bash
/usr/local/bin/docker ps -aq --filter label=pirun.suite=jdbc_oracle_container
```

Expected:

```text
No container ids are printed.
```

- [ ] **Step 4: Commit Oracle evidence if the run was requested for acceptance reporting**

```bash
git add .pirun/runs/<run_id>/jdbc_oracle_container/project_report.json \
        .pirun/runs/<run_id>/jdbc_oracle_container/provisioning_evidence.yaml \
        .pirun/runs/<run_id>/jdbc_oracle_container/dialect_probe.yaml \
        .pirun/runs/<run_id>/jdbc_oracle_container/cleanup_evidence.yaml
git commit -m "test: add oracle heavy jdbc pirun evidence"
```

## Task 8: Manual DB2 Verification on Dedicated Runner

**Files:**
- Runtime output: `.pirun/runs/<run_id>/jdbc_db2_container/`
- Report output: `.pirun/runs/<run_id>/jdbc_db2_container/project_report.json`

- [ ] **Step 1: Check DB2 resource gates without starting DB2**

Run:

```bash
/usr/local/bin/docker info --format '{{.MemTotal}}'
df -g .
```

Expected:

```text
Docker memory is at least 8589934592 bytes.
Free disk is at least 40 GiB.
```

- [ ] **Step 2: Run DB2 only on a dedicated runner**

Run:

```bash
PIRUN_ENABLE_HEAVY_DB_CONTAINERS=1 \
PIRUN_ACCEPT_DB2_LICENSE=1 \
PIRUN_ALLOW_PRIVILEGED_DB2=1 \
PYTHONDONTWRITEBYTECODE=1 \
python3 pirun/run_heavy_jdbc_container.py --db db2 --framework-version 0.2.5
```

Expected:

```text
Exit code 0 only when project_report.json result_classification is PASS.
If result_classification is PROJECT_PROVISIONING_PASS_FRAMEWORK_CONSUMPTION_NOT_PROVEN, exit code is non-zero because framework JDBC provider consumption was not proven.
dialect_probe.yaml dialect_probe_status is passed.
cleanup_evidence.yaml cleanup_status is passed.
```

- [ ] **Step 3: Confirm no DB2 container remains**

Run:

```bash
/usr/local/bin/docker ps -aq --filter label=pirun.suite=jdbc_db2_container
```

Expected:

```text
No container ids are printed.
```

- [ ] **Step 4: Commit DB2 evidence if the run was requested for acceptance reporting**

```bash
git add .pirun/runs/<run_id>/jdbc_db2_container/project_report.json \
        .pirun/runs/<run_id>/jdbc_db2_container/provisioning_evidence.yaml \
        .pirun/runs/<run_id>/jdbc_db2_container/dialect_probe.yaml \
        .pirun/runs/<run_id>/jdbc_db2_container/cleanup_evidence.yaml
git commit -m "test: add db2 heavy jdbc pirun evidence"
```

## Task 9: Final Verification

**Files:**
- All files modified in prior tasks

- [ ] **Step 1: Run lightweight verification**

Run:

```bash
git diff --check
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
```

Expected:

```text
48 or more tests run.
OK
```

- [ ] **Step 2: Verify skip behavior on default machine**

Run:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pirun/run_heavy_jdbc_container.py --db oracle --framework-version 0.2.5
PYTHONDONTWRITEBYTECODE=1 python3 pirun/run_heavy_jdbc_container.py --db db2 --framework-version 0.2.5
```

Expected:

```text
Both commands exit 0.
Both write project_report.json.
Both classify as SKIPPED_POLICY_GATE.
No Docker container is started.
```

- [ ] **Step 3: Verify repository status**

Run:

```bash
git status --short --branch
```

Expected:

```text
## codex/pi-run-full-scope...origin/codex/pi-run-full-scope
```

No unstaged or untracked files remain unless runtime evidence was intentionally generated and selected for review.

## Self-Review

- Spec coverage: PASS. The plan covers project-side provisioning, resource gates, policy gates, Oracle mode, DB2 mode, external JDBC materialization, framework-consumption classification, cleanup, manual Oracle run, manual DB2 run, and final verification.
- Placeholder scan: PASS. Every task names concrete files, commands, expected outcomes, and code blocks for changed code.
- Type consistency: PASS. The runner imports and function names match the created provisioner/materializer helpers.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-07-09-heavy-jdbc-container-pirun.md`.

Two execution options:

1. Subagent-Driven (recommended): dispatch a fresh subagent per task, review between tasks, and keep changes small.
2. Inline Execution: execute tasks in this session with checkpoints after each commit-sized task.
