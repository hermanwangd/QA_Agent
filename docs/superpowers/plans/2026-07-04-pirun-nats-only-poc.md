# PI-run NATS-only Provisioning POC Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a project-side NATS-only provisioning and materialization POC that starts Docker NATS, writes a materialized standard framework workspace, invokes the v0.2.2 framework jar unchanged, records provisioning evidence, and always cleans up.

**Architecture:** The PI-run project owns Docker lifecycle and artifact materialization. The framework jar remains unchanged and receives only standard `suite_manifest.yaml`, `env_profiles/ci.yaml`, and `environment_bindings/ci.yaml` files from `.pirun/runs/<run_id>/contract_baseline/`.

**Tech Stack:** Python 3 standard library, `/usr/local/bin/docker`, NATS Docker image `nats:2.10-alpine`, v0.2.2 release jar with `-Xmx512m`, PyYAML for YAML read/write.

---

## Constraints

- Do not add framework `--binding-overrides`.
- Do not add framework generated-ref consumer logic.
- Do not introduce Python `testcontainers` package in the POC.
- Keep Java commands at `-Xmx512m`.
- Respect the 8G machine safety limit.
- Use one orchestrator so cleanup runs on failure.

## File Structure

- Create: `pirun/__init__.py`
- Create: `pirun/docker_cli.py`
  - Small wrapper around `/usr/local/bin/docker`.
  - Adds labels and resource limits.
- Create: `pirun/provisioners/__init__.py`
- Create: `pirun/provisioners/nats.py`
  - Starts/stops NATS.
  - Checks readiness with Docker port mapping and TCP connect.
- Create: `pirun/materialize/__init__.py`
- Create: `pirun/materialize/contract_baseline.py`
  - Copies usage-kit contract baseline files to `.pirun/runs/<run_id>/contract_baseline/`.
  - Rewrites generated NATS refs to `env://PIRUN_NATS_CONNECTION`.
  - Leaves DB/WireMock out of NATS-only mode or marks them non-selected for POC input.
- Create: `pirun/run_contract_baseline.py`
  - Single orchestrator.
  - `try/finally` cleanup.
  - Writes `.pirun/runs/<run_id>/contract_baseline/provisioning_evidence.yaml`.
  - Invokes framework jar.
- Create: `tests/test_pirun_materialize.py`
- Create: `tests/test_pirun_docker_cli.py`
- Modify: `.gitignore`
  - Ignore `.pirun/runs/**/secrets/*`, `.pirun/secrets/*`, and runtime logs while allowing `.gitkeep`.

## Task 1: Add Docker CLI Wrapper

**Files:**
- Create: `pirun/__init__.py`
- Create: `pirun/docker_cli.py`
- Test: `tests/test_pirun_docker_cli.py`

- [ ] **Step 1: Write tests**

Create `tests/test_pirun_docker_cli.py`:

```python
import unittest

from pirun.docker_cli import build_docker_run_command


class DockerCliTests(unittest.TestCase):
    def test_build_nats_run_command_has_labels_and_limits(self):
        cmd = build_docker_run_command(
            run_id="RUN-TEST",
            suite="contract_baseline",
            name="pirun-RUN-TEST-nats",
            image="nats:2.10-alpine",
            ports={"4222/tcp": 0},
            memory="256m",
        )

        joined = " ".join(cmd)
        self.assertIn("/usr/local/bin/docker", cmd[0])
        self.assertIn("--label", cmd)
        self.assertIn("pirun.run_id=RUN-TEST", cmd)
        self.assertIn("pirun.suite=contract_baseline", cmd)
        self.assertIn("--memory", cmd)
        self.assertIn("256m", cmd)
        self.assertIn("nats:2.10-alpine", cmd)
        self.assertIn("-p", cmd)
        self.assertIn("127.0.0.1::4222", joined)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```sh
python3 -m unittest tests/test_pirun_docker_cli.py
```

Expected: import failure because `pirun/docker_cli.py` does not exist.

- [ ] **Step 3: Implement wrapper**

Create `pirun/__init__.py` as an empty file.

Create `pirun/docker_cli.py`:

```python
from __future__ import annotations

import subprocess
from dataclasses import dataclass


DOCKER = "/usr/local/bin/docker"


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
    )
    return CommandResult(proc.returncode, proc.stdout, proc.stderr)


def build_docker_run_command(
    *,
    run_id: str,
    suite: str,
    name: str,
    image: str,
    ports: dict[str, int],
    memory: str,
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
    for container_port, host_port in sorted(ports.items()):
        host = f"127.0.0.1:{host_port}:{container_port.split('/')[0]}" if host_port else f"127.0.0.1::{container_port.split('/')[0]}"
        cmd.extend(["-p", host])
    cmd.append(image)
    return cmd


def remove_by_label(run_id: str) -> CommandResult:
    list_cmd = [DOCKER, "ps", "-aq", "--filter", f"label=pirun.run_id={run_id}"]
    listed = run_command(list_cmd)
    ids = [line.strip() for line in listed.stdout.splitlines() if line.strip()]
    if not ids:
        return CommandResult(0, "", "")
    return run_command([DOCKER, "rm", "-f", *ids], timeout=60)
```

- [ ] **Step 4: Run test**

Run:

```sh
python3 -m unittest tests/test_pirun_docker_cli.py
```

Expected: pass.

## Task 2: Add NATS Provisioner

**Files:**
- Create: `pirun/provisioners/__init__.py`
- Create: `pirun/provisioners/nats.py`
- Test: manual Docker smoke command

- [ ] **Step 1: Implement NATS provisioner**

Create `pirun/provisioners/__init__.py` as an empty file.

Create `pirun/provisioners/nats.py`:

```python
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


def start_nats(run_id: str) -> NatsProvisionResult:
    name = f"pirun-{run_id}-nats"
    cmd = build_docker_run_command(
        run_id=run_id,
        suite="contract_baseline",
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
        provider_id="nats-event-bus",
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
```

- [ ] **Step 2: Docker smoke test**

Run:

```sh
python3 - <<'PY'
from pirun.provisioners.nats import start_nats, stop_run
run_id = "SMOKE-NATS"
try:
    result = start_nats(run_id)
    print(result)
finally:
    stop_run(run_id)
PY
/usr/local/bin/docker ps --filter label=pirun.run_id=SMOKE-NATS --format '{{.ID}}'
```

Expected: first command prints `NatsProvisionResult`; second command prints nothing.

## Task 3: Add Contract Baseline Materializer

**Files:**
- Create: `pirun/materialize/__init__.py`
- Create: `pirun/materialize/contract_baseline.py`
- Test: `tests/test_pirun_materialize.py`
- Modify: `.gitignore`

- [ ] **Step 1: Write tests**

Create `tests/test_pirun_materialize.py`:

```python
import tempfile
import unittest
from pathlib import Path

from pirun.materialize.contract_baseline import materialize_nats_only


class MaterializeTests(unittest.TestCase):
    def test_materialize_nats_only_writes_standard_artifacts_without_generated_refs(self):
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "contract_baseline"
            materialize_nats_only(
                run_dir=run_dir,
                nats_subject="payments.accepted",
            )

            env_binding = run_dir / "environment_bindings" / "ci.yaml"
            env_profile = run_dir / "env_profiles" / "ci.yaml"
            suite = run_dir / "suite_manifest.yaml"

            self.assertTrue(env_binding.exists())
            self.assertTrue(env_profile.exists())
            self.assertTrue(suite.exists())

            combined = "\\n".join(p.read_text() for p in [env_binding, env_profile, suite])
            self.assertNotIn("generated://", combined)
            self.assertIn("env://PIRUN_NATS_CONNECTION", combined)
            self.assertIn("provider_id: nats-event-bus", env_binding.read_text())


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test and confirm failure**

Run:

```sh
python3 -m unittest tests/test_pirun_materialize.py
```

Expected: import failure.

- [ ] **Step 3: Implement materializer**

Create `pirun/materialize/__init__.py` as an empty file.

Create `pirun/materialize/contract_baseline.py`:

```python
from __future__ import annotations

import shutil
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE = REPO_ROOT / "usage-kit-v0.2.2" / "usage-kit" / "samples" / "contract_baseline"


def materialize_nats_only(*, run_dir: Path, nats_subject: str) -> None:
    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(SOURCE, run_dir)

    env_binding_path = run_dir / "environment_bindings" / "ci.yaml"
    env_profile_path = run_dir / "env_profiles" / "ci.yaml"

    env_binding = yaml.safe_load(env_binding_path.read_text()) or {}
    env_binding["environment_id"] = "ci-contract-sample-nats-only"
    env_binding["provider_bindings"] = [
        {
            "provider_id": "nats-event-bus",
            "runtime_mode": "ephemeral",
            "binding_values": {
                "connection": {"secret_ref": "env://PIRUN_NATS_CONNECTION"},
                "subject": nats_subject,
                "timeout": "PT30S",
                "poll_interval": "PT0.5S",
            },
        }
    ]
    env_binding_path.write_text(yaml.safe_dump(env_binding, sort_keys=False), encoding="utf-8")

    env_profile = yaml.safe_load(env_profile_path.read_text()) or {}
    env_profile["providers"] = {
        "nats-event-bus": {
            "runtime_mode": "ephemeral",
            "binding_keys": {
                "connection": {"secret_ref": "env://PIRUN_NATS_CONNECTION"},
                "subject": {"value": nats_subject},
                "timeout": {"value": "PT30S"},
                "poll_interval": {"value": "PT0.5S"},
            },
        }
    }
    env_profile_path.write_text(yaml.safe_dump(env_profile, sort_keys=False), encoding="utf-8")
```

- [ ] **Step 4: Update `.gitignore`**

Add:

```gitignore
.pirun/runs/
.pirun/secrets/*
!.pirun/secrets/.gitkeep
```

- [ ] **Step 5: Run materializer tests**

Run:

```sh
python3 -m unittest tests/test_pirun_materialize.py
```

Expected: pass.

## Task 4: Add Orchestrator

**Files:**
- Create: `pirun/run_contract_baseline.py`
- Test: manual orchestrator smoke command

- [ ] **Step 1: Implement orchestrator**

Create `pirun/run_contract_baseline.py`:

```python
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

import yaml

from pirun.materialize.contract_baseline import materialize_nats_only
from pirun.provisioners.nats import start_nats, stop_run


REPO_ROOT = Path(__file__).resolve().parents[1]
JAR = REPO_ROOT / "release-assets-v0.2.2" / "spec-driven-auto-regression-0.2.2.jar"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default="ci")
    parser.add_argument("--mode", choices=["nats-only"], default="nats-only")
    parser.add_argument("--run-id", default=f"PIRUN-{int(time.time())}")
    args = parser.parse_args()

    run_root = REPO_ROOT / ".pirun" / "runs" / args.run_id / "contract_baseline"
    provisioning = None
    framework = {"invoked": False}
    cleanup = {"status": "not_started"}

    try:
        nats = start_nats(args.run_id)
        provisioning = {
            "provider_id": nats.provider_id,
            "image": nats.image,
            "container_id": nats.container_id,
            "mapped_ports": {"4222": nats.port},
            "readiness": {"status": nats.readiness_status, "check": "tcp_connect"},
        }
        materialize_nats_only(run_dir=run_root, nats_subject="payments.accepted")

        env = os.environ.copy()
        env["PIRUN_NATS_CONNECTION"] = nats.connection_url
        cmd = [
            "java",
            "-Xmx512m",
            "-jar",
            str(JAR),
            "run",
            "--suite",
            str(run_root / "suite_manifest.yaml"),
            "--profile",
            args.profile,
        ]
        proc = subprocess.run(cmd, cwd=str(REPO_ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        framework = {
            "invoked": True,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
        return proc.returncode
    finally:
        try:
            stop_run(args.run_id)
            cleanup = {"status": "passed"}
        except Exception as exc:
            cleanup = {"status": "failed", "error": str(exc)}
        write_project_report(args.run_id, run_root, provisioning, framework, cleanup)


def write_project_report(run_id: str, run_root: Path, provisioning, framework, cleanup) -> None:
    run_root.mkdir(parents=True, exist_ok=True)
    report = {
        "project_provisioning_report_version": "v0.1",
        "run_id": run_id,
        "profile": "ci",
        "project_provisioning_status": "passed" if provisioning else "failed",
        "materialization_status": "passed" if (run_root / "suite_manifest.yaml").exists() else "failed",
        "framework_invoked": bool(framework.get("invoked")),
        "framework_result": {
            "exit_code": framework.get("exit_code"),
            "known_blocker": "CONTRACT_UNSUPPORTED_SUITE_RUNTIME" in framework.get("stdout", ""),
        },
        "dependencies": [provisioning] if provisioning else [],
        "cleanup_status": cleanup["status"],
        "evidence_classification": "local_ci_ephemeral_only",
        "downstream_release_evidence": False,
    }
    (run_root / "provisioning_evidence.yaml").write_text(yaml.safe_dump(report, sort_keys=False), encoding="utf-8")
    (run_root / "framework_stdout.txt").write_text(framework.get("stdout", ""), encoding="utf-8")
    (run_root / "framework_stderr.txt").write_text(framework.get("stderr", ""), encoding="utf-8")
    (run_root / "project_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run orchestrator smoke**

Run:

```sh
python3 pirun/run_contract_baseline.py --profile ci --mode nats-only --run-id SMOKE-NATS-ORCH || true
/usr/local/bin/docker ps --filter label=pirun.run_id=SMOKE-NATS-ORCH --format '{{.ID}}'
test -f .pirun/runs/SMOKE-NATS-ORCH/contract_baseline/provisioning_evidence.yaml
sed -n '1,120p' .pirun/runs/SMOKE-NATS-ORCH/contract_baseline/provisioning_evidence.yaml
```

Expected:

- Docker `ps` prints nothing.
- Provisioning evidence exists.
- If framework still blocks, project report has `known_blocker: true`.

## Task 5: Final Verification

**Files:**
- All project POC files

- [ ] **Step 1: Run unit tests**

Run:

```sh
python3 -m unittest tests/test_pirun_docker_cli.py tests/test_pirun_materialize.py
```

Expected: all pass.

- [ ] **Step 2: Run Docker cleanup check**

Run:

```sh
/usr/local/bin/docker ps --filter label=pirun.suite=contract_baseline --format '{{.ID}}'
```

Expected: no output.

- [ ] **Step 3: Check git status**

Run:

```sh
git status --short --branch
```

Expected: only planned local files and ignored `.pirun/runs` artifacts.

## Risks

- v0.2.2 framework may still block before provider runtime with `CONTRACT_UNSUPPORTED_SUITE_RUNTIME`; that is acceptable for this project-side POC if provisioning, materialization, framework invocation, and cleanup all succeed.
- `env://PIRUN_NATS_CONNECTION` may not be accepted for NATS connection by current runtime; if so, record the failure and update the materializer only after verifying supported secret-ref semantics.
- NATS image pull may take time on first run; keep no parallel Docker pulls.
