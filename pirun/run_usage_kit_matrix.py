from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.inspect_usage_kit import inspect_usage_kit
from pirun.run_contract_baseline import framework_paths
from pirun.redaction import redact_text


DEFAULT_COMMAND_SET = ("validate",)


def build_matrix_plan(
    inspection: dict[str, Any],
    *,
    framework_jar: Path,
    usage_kit_root: Path,
    command_set: tuple[str, ...] = DEFAULT_COMMAND_SET,
) -> dict[str, Any]:
    suites: dict[str, dict[str, Any]] = {}
    blocked_rows = []

    for row in inspection["matrix_rows"]:
        if row.get("runnable_now") and row.get("expected_status") == "PASS":
            for suite in row.get("sample_paths") or []:
                if not suite.endswith("suite_manifest.yaml"):
                    continue
                entry = suites.setdefault(
                    suite,
                    {
                        "suite": suite,
                        "commands": list(command_set),
                        "providers": [],
                    },
                )
                entry["providers"].append(
                    {
                        "provider_type": row["provider_type"],
                        "runtime_mode": row["runtime_mode"],
                    }
                )
        else:
            blocked_rows.append(
                {
                    "provider_type": row["provider_type"],
                    "runtime_mode": row["runtime_mode"],
                    "expected_status": row["expected_status"],
                    "reason": row["reason"],
                }
            )

    return {
        "framework_jar": str(framework_jar),
        "usage_kit_root": str(usage_kit_root),
        "command_set": list(command_set),
        "runnable_suites": [suites[key] for key in sorted(suites)],
        "blocked_rows": sorted(
            blocked_rows,
            key=lambda row: (row["expected_status"], row["provider_type"], row["runtime_mode"]),
        ),
    }


def run_matrix_plan(plan: dict[str, Any], *, execute: bool = False) -> dict[str, Any]:
    suite_results = []
    executed_command_count = 0

    for suite in plan["runnable_suites"]:
        for command_name in suite["commands"]:
            result = _run_suite_command(
                framework_jar=Path(plan["framework_jar"]),
                usage_kit_root=Path(plan["usage_kit_root"]),
                suite=suite["suite"],
                command_name=command_name,
                execute=execute,
            )
            suite_results.append(result)
            if result["status"] != "PLANNED":
                executed_command_count += 1

    unexpected_failures = sum(1 for result in suite_results if result["status"] == "FAIL")
    planned_command_count = sum(len(suite["commands"]) for suite in plan["runnable_suites"])
    return {
        "summary": {
            "planned_suite_count": len(plan["runnable_suites"]),
            "planned_command_count": planned_command_count,
            "executed_command_count": executed_command_count,
            "unexpected_failures": unexpected_failures,
            "blocked_row_count": len(plan["blocked_rows"]),
        },
        "suite_results": suite_results,
        "blocked_rows": plan["blocked_rows"],
    }


def write_run_report(report: dict[str, Any], output_dir: Path, *, version: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_version = version.removeprefix("v")
    json_path = output_dir / f"pi-run-v{clean_version}-usage-kit-matrix-run-report.json"
    markdown_path = output_dir / f"pi-run-v{clean_version}-full-coverage-report.md"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report, clean_version), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _run_suite_command(
    *,
    framework_jar: Path,
    usage_kit_root: Path,
    suite: str,
    command_name: str,
    execute: bool,
) -> dict[str, Any]:
    command_args = shlex.split(command_name)
    command = ["java", "-Xmx512m", "-jar", str(framework_jar), *command_args, "--suite", suite]
    if _needs_profile(command_args):
        command.extend(["--profile", _suite_profile(usage_kit_root / suite)])
    base = {
        "suite": suite,
        "command": command_name,
        "argv": command,
    }
    if not execute:
        return {**base, "status": "PLANNED", "exit_code": None, "stdout": "", "stderr": ""}

    proc = subprocess.run(
        command,
        cwd=str(usage_kit_root),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return {
        **base,
        "status": "PASS" if proc.returncode == 0 else "FAIL",
        "exit_code": proc.returncode,
        "stdout": redact_text(proc.stdout),
        "stderr": redact_text(proc.stderr),
    }


def _needs_profile(command_args: list[str]) -> bool:
    return bool(command_args and command_args[0] == "run" and "--profile" not in command_args)


def _suite_profile(suite_path: Path) -> str:
    payload = yaml.safe_load(suite_path.read_text(encoding="utf-8")) or {}
    if payload.get("profile"):
        return payload["profile"]
    profiles = payload.get("profiles") or []
    if profiles:
        return profiles[0]
    return "local"


def _markdown_report(report: dict[str, Any], version: str) -> str:
    summary = report["summary"]
    lines = [
        f"# pi-run v{version} Full Coverage Report",
        "",
        "## Summary",
        "",
        f"- Planned suite count: `{summary['planned_suite_count']}`",
        f"- Planned command count: `{summary.get('planned_command_count', len(report['suite_results']))}`",
        f"- Executed command count: `{summary['executed_command_count']}`",
        f"- Unexpected failures: `{summary['unexpected_failures']}`",
        f"- Blocked row count: `{summary['blocked_row_count']}`",
        "",
        "## Suite Results",
        "",
        "| Suite | Command | Status | Exit Code |",
        "|---|---|---:|---:|",
    ]
    for result in report["suite_results"]:
        exit_code = "" if result["exit_code"] is None else str(result["exit_code"])
        lines.append(
            f"| `{result['suite']}` | `{result['command']}` | `{result['status']}` | {exit_code} |"
        )

    lines.extend(
        [
            "",
            "## Blocked Rows",
            "",
            "| Provider Type | Runtime Mode | Expected Status | Reason |",
            "|---|---|---|---|",
        ]
    )
    for row in report["blocked_rows"]:
        lines.append(
            f"| `{row['provider_type']}` | `{row['runtime_mode']}` | `{row['expected_status']}` | {row['reason']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-version", default="0.2.3")
    parser.add_argument("--matrix-json", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--command-set",
        default="validate",
        help="Comma-separated commands, for example: validate,run --dry-run,run",
    )
    args = parser.parse_args(argv)

    paths = framework_paths(args.framework_version)
    if args.matrix_json:
        inspection = json.loads(args.matrix_json.read_text(encoding="utf-8"))
    else:
        inspection = inspect_usage_kit(paths.usage_kit_root)

    command_set = tuple(command.strip() for command in args.command_set.split(",") if command.strip())
    plan = build_matrix_plan(
        inspection,
        framework_jar=paths.jar,
        usage_kit_root=paths.usage_kit_root,
        command_set=command_set,
    )
    report = run_matrix_plan(plan, execute=args.execute)
    outputs = write_run_report(report, args.output_dir, version=args.framework_version)
    print(f"run_report_json: {outputs['json']}")
    print(f"full_coverage_report: {outputs['markdown']}")
    print(f"planned_suite_count: {report['summary']['planned_suite_count']}")
    print(f"unexpected_failures: {report['summary']['unexpected_failures']}")
    return 1 if report["summary"]["unexpected_failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
