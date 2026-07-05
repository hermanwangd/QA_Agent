#!/usr/bin/env python3
"""Run the v0.2.2 release-asset PI-run matrix sequentially."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if __package__ in {None, ""}:
    sys.path.insert(0, str(REPO_ROOT))

from pirun.framework_paths import framework_paths


FRAMEWORK_PATHS = framework_paths("0.2.2", repo_root=REPO_ROOT)
USAGE_KIT = FRAMEWORK_PATHS.usage_kit_root
SAMPLES = USAGE_KIT / "samples"
JAR = FRAMEWORK_PATHS.jar
OUT_JSON = REPO_ROOT / "reports" / "pi-run-v0.2.2-exhaustive-matrix.json"
OUT_MD = REPO_ROOT / "reports" / "pi-run-v0.2.2-exhaustive-matrix.md"


@dataclass
class CommandResult:
    name: str
    command: list[str]
    cwd: str
    exit_code: int
    duration_seconds: float
    stdout: str
    stderr: str
    status_fields: dict[str, str]
    expectation: str
    ok: bool


@dataclass
class SuiteEntry:
    suite_path: str
    suite_id: str
    profile: str
    kind: str
    expected_run: str
    tests: int
    children: int
    provider_types: list[str]
    operations: list[str]
    verify_types: list[str]


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def status_fields(text: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in text.splitlines():
        match = re.match(r"^([A-Za-z0-9_.-]+):\s*(.+?)\s*$", line.strip())
        if match:
            key, value = match.groups()
            if key in {
                "validation_status",
                "run_status",
                "report_status",
                "evidence_validation_status",
                "suite_id",
                "batch_id",
                "run_id",
                "result_json",
                "failure_code",
                "status",
                "test_count",
                "passed_count",
                "failed_count",
            }:
                fields[key] = value
    return fields


def run_command(name: str, command: list[str], cwd: Path, expectation: str) -> CommandResult:
    started = time.monotonic()
    proc = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )
    duration = time.monotonic() - started
    fields = status_fields(proc.stdout)
    ok = classify_ok(name, proc.returncode, fields, expectation)
    return CommandResult(
        name=name,
        command=command,
        cwd=str(cwd),
        exit_code=proc.returncode,
        duration_seconds=round(duration, 3),
        stdout=proc.stdout,
        stderr=proc.stderr,
        status_fields=fields,
        expectation=expectation,
        ok=ok,
    )


def classify_ok(name: str, exit_code: int, fields: dict[str, str], expectation: str) -> bool:
    if expectation == "positive":
        return exit_code == 0
    if expectation == "negative-run":
        return exit_code != 0 and fields.get("run_status") in {"failed", "blocked"}
    if expectation == "blocked-contract-baseline":
        return (
            exit_code != 0
            and fields.get("run_status") == "blocked"
            and fields.get("failure_code") == "CONTRACT_UNSUPPORTED_SUITE_RUNTIME"
        )
    if expectation == "profile-negative":
        return exit_code != 0 and "CONFIGURATION_PROFILE_MISMATCH" in fields.values()
    if expectation == "report-positive":
        return exit_code == 0 and fields.get("report_status", "").startswith("review_ready")
    if expectation == "known-report-blocker":
        return exit_code != 0 and fields.get("report_status") == "invalid"
    if expectation == "report-negative":
        return exit_code != 0 and fields.get("report_status") == "invalid"
    if expectation == "evidence-positive":
        return exit_code == 0 and fields.get("evidence_validation_status") == "passed"
    if expectation == "evidence-negative":
        return exit_code != 0 and fields.get("evidence_validation_status") == "failed"
    return exit_code == 0


def collect_provider_types(suite_dir: Path) -> list[str]:
    values: set[str] = set()
    for path in sorted((suite_dir / "provider_instances").glob("*.yaml")):
        data = load_yaml(path)
        value = data.get("provider_type")
        if value:
            values.add(str(value))
    return sorted(values)


def collect_test_case_features(suite_dir: Path, manifest: dict[str, Any]) -> tuple[list[str], list[str]]:
    operations: set[str] = set()
    verify_types: set[str] = set()
    for test_ref in manifest.get("tests") or []:
        path = suite_dir / str(test_ref)
        if not path.exists():
            continue
        data = load_yaml(path)
        cases = data.get("test_cases") or ([data] if data.get("test_case_id") else [])
        for case in cases:
            for op in (case.get("execute") or {}).get("operations") or []:
                value = op.get("operation") or op.get("action") or op.get("type")
                if value:
                    operations.add(str(value))
            for check in (case.get("verify") or {}).get("checks") or []:
                value = check.get("type") or check.get("kind") or check.get("operator")
                if value:
                    verify_types.add(str(value))
    return sorted(operations), sorted(verify_types)


def manifest_kind(path: Path, manifest: dict[str, Any]) -> str:
    if manifest.get("child_suites"):
        return "suite-group"
    name = path.name
    if "failure" in name:
        return "negative-suite"
    if "boundary" in name:
        return "boundary-suite"
    if "contract_baseline" in str(path):
        return "contract-baseline"
    return "positive-suite"


def expected_run(kind: str) -> str:
    if kind == "negative-suite":
        return "negative-run"
    if kind == "contract-baseline":
        return "blocked-contract-baseline"
    return "positive"


def inventory() -> list[SuiteEntry]:
    entries: list[SuiteEntry] = []
    for path in sorted(SAMPLES.rglob("suite_manifest*.yaml")):
        manifest = load_yaml(path)
        profiles = manifest.get("profiles") or ([manifest.get("profile")] if manifest.get("profile") else [])
        suite_dir = path.parent
        kind = manifest_kind(path, manifest)
        operations, verify_types = collect_test_case_features(suite_dir, manifest)
        provider_types = collect_provider_types(suite_dir)
        for profile in profiles:
            entries.append(
                SuiteEntry(
                    suite_path=str(path.relative_to(USAGE_KIT)),
                    suite_id=str(manifest.get("suite_id")),
                    profile=str(profile),
                    kind=kind,
                    expected_run=expected_run(kind),
                    tests=len(manifest.get("tests") or []),
                    children=len(manifest.get("child_suites") or []),
                    provider_types=provider_types,
                    operations=operations,
                    verify_types=verify_types,
                )
            )
    return entries


def java_command(*args: str) -> list[str]:
    return ["java", "-Xmx512m", "-jar", str(JAR), *args]


def run_suite_matrix(entries: list[SuiteEntry]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entry in entries:
        suite = entry.suite_path
        profile = entry.profile
        row: dict[str, Any] = {"entry": asdict(entry), "commands": []}
        row["commands"].append(
            asdict(
                run_command(
                    "validate",
                    java_command("validate", "--suite", suite, "--profile", profile),
                    USAGE_KIT,
                    "positive",
                )
            )
        )
        row["commands"].append(
            asdict(
                run_command(
                    "dry-run",
                    java_command("run", "--suite", suite, "--profile", profile, "--dry-run"),
                    USAGE_KIT,
                    "positive",
                )
            )
        )
        row["commands"].append(
            asdict(
                run_command(
                    "run",
                    java_command("run", "--suite", suite, "--profile", profile),
                    USAGE_KIT,
                    entry.expected_run,
                )
            )
        )
        rows.append(row)
    return rows


def collect_result_jsons() -> list[Path]:
    return sorted(USAGE_KIT.glob("target/**/result.json")) + sorted(REPO_ROOT.glob("target/**/result.json"))


def run_result_gates(paths: list[Path]) -> list[dict[str, Any]]:
    gates: list[dict[str, Any]] = []
    for path in paths:
        if path.is_relative_to(USAGE_KIT):
            cwd = USAGE_KIT
            rel = str(path.relative_to(USAGE_KIT))
        else:
            cwd = REPO_ROOT
            rel = str(path.relative_to(REPO_ROOT))
        gate: dict[str, Any] = {"result_json": rel, "commands": []}
        gate["commands"].append(
            asdict(
                run_command(
                    "validate-evidence",
                    java_command("validate-evidence", "--result", rel),
                    cwd,
                    "evidence-positive",
                )
            )
        )
        report = run_command(
            "report-yaml",
            java_command("report", "--result", rel, "--format", "yaml"),
            cwd,
            "report-positive",
        )
        if report.exit_code != 0 and "VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM" in report.stdout:
            report.expectation = "known-report-blocker"
            report.ok = classify_ok(report.name, report.exit_code, report.status_fields, report.expectation)
        gate["commands"].append(asdict(report))
        gates.append(gate)
    return gates


def write_markdown(payload: dict[str, Any]) -> None:
    def display(cmd: dict[str, Any]) -> str:
        if cmd["expectation"] == "blocked-contract-baseline" and cmd["ok"]:
            return "BLOCKED(expected)"
        if cmd["expectation"] == "negative-run" and cmd["ok"]:
            return "FAIL(expected)"
        if cmd["ok"]:
            return "OK"
        return f"FAIL({cmd['exit_code']})"

    lines: list[str] = []
    lines.append("# PI-run v0.2.2 Exhaustive Matrix")
    lines.append("")
    lines.append(f"Inventory count: {len(payload['inventory'])}")
    suite_commands = [cmd for row in payload["suite_matrix"] for cmd in row["commands"]]
    result_commands = [cmd for row in payload["result_gates"] for cmd in row["commands"]]
    failed = [cmd for cmd in suite_commands + result_commands if not cmd["ok"]]
    known = [cmd for cmd in result_commands if cmd["expectation"] == "known-report-blocker"]
    lines.append(f"Suite commands: {len(suite_commands)}")
    lines.append(f"Result gate commands: {len(result_commands)}")
    lines.append(f"Unexpected command failures: {len(failed)}")
    lines.append(f"Known report blockers: {len(known)}")
    lines.append("")
    lines.append("## Suite Matrix")
    lines.append("")
    lines.append("| Suite | Profile | Kind | Validate | Dry-run | Run |")
    lines.append("|---|---|---|---:|---:|---:|")
    for row in payload["suite_matrix"]:
        entry = row["entry"]
        by_name = {cmd["name"]: cmd for cmd in row["commands"]}
        lines.append(
            "| {suite} | {profile} | {kind} | {validate} | {dry} | {run} |".format(
                suite=entry["suite_path"],
                profile=entry["profile"],
                kind=entry["kind"],
                validate=display(by_name["validate"]),
                dry=display(by_name["dry-run"]),
                run=display(by_name["run"]),
            )
        )
    lines.append("")
    lines.append("## Unexpected Failures")
    lines.append("")
    if failed:
        for cmd in failed:
            lines.append(f"- `{cmd['name']}` exit {cmd['exit_code']} expectation `{cmd['expectation']}`")
    else:
        lines.append("- None")
    lines.append("")
    lines.append("## Known Report Blockers")
    lines.append("")
    if known:
        for cmd in known:
            lines.append(f"- `{cmd['command'][-3]}`: `VALIDATION_MOCK_RELEASE_EVIDENCE_CLAIM`")
    else:
        lines.append("- None")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def summarize(path: Path) -> int:
    payload = json.loads(path.read_text(encoding="utf-8"))
    suite_commands = [cmd for row in payload["suite_matrix"] for cmd in row["commands"]]
    result_commands = [cmd for row in payload["result_gates"] for cmd in row["commands"]]
    failed = [cmd for cmd in suite_commands + result_commands if not cmd["ok"]]
    known = [cmd for cmd in result_commands if cmd["expectation"] == "known-report-blocker"]
    print(f"inventory_count: {len(payload['inventory'])}")
    print(f"suite_commands: {len(suite_commands)}")
    print(f"result_gate_commands: {len(result_commands)}")
    print(f"unexpected_failures: {len(failed)}")
    print(f"known_report_blockers: {len(known)}")
    for cmd in failed[:20]:
        print(f"failure: {cmd['name']} exit={cmd['exit_code']} expectation={cmd['expectation']}")
    return 0 if not failed else 1


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory-only", action="store_true")
    parser.add_argument("--run-all", action="store_true")
    parser.add_argument("--summarize")
    args = parser.parse_args(argv)

    if args.summarize:
        return summarize(Path(args.summarize))

    entries = inventory()
    if args.inventory_only:
        print(f"inventory_count: {len(entries)}")
        for entry in entries:
            print(f"{entry.suite_path} profile={entry.profile} kind={entry.kind}")
        return 0

    if args.run_all:
        suite_matrix = run_suite_matrix(entries)
        result_gates = run_result_gates(collect_result_jsons())
        payload = {
            "jar": str(JAR.relative_to(REPO_ROOT)),
            "usage_kit": str(USAGE_KIT.relative_to(REPO_ROOT)),
            "inventory": [asdict(entry) for entry in entries],
            "suite_matrix": suite_matrix,
            "result_gates": result_gates,
        }
        OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        write_markdown(payload)
        print(f"inventory_count: {len(entries)}")
        print(f"matrix_written: {OUT_JSON.relative_to(REPO_ROOT)}")
        print(f"markdown_written: {OUT_MD.relative_to(REPO_ROOT)}")
        return summarize(OUT_JSON)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
