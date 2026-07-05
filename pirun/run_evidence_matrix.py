from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.run_contract_baseline import framework_paths
from pirun.redaction import redact_text


VALID_RESULT = "samples/evidence_hardening/valid_result.json"
INVALID_MISSING_EVIDENCE = "samples/evidence_hardening/invalid_missing_evidence_result.json"
INVALID_SECRET_LEAK = "samples/evidence_hardening/invalid_secret_leak_result.json"
SUPPORTED_REPORT_FORMATS = ("text", "yaml")


def build_evidence_cases() -> list[dict[str, Any]]:
    cases = [
        _case("validate-evidence-valid", ["validate-evidence", "--result", VALID_RESULT], 0, "validate-evidence-positive"),
        _case(
            "validate-evidence-missing-evidence",
            ["validate-evidence", "--result", INVALID_MISSING_EVIDENCE],
            1,
            "validate-evidence-negative",
        ),
        _case(
            "validate-evidence-secret-leak",
            ["validate-evidence", "--result", INVALID_SECRET_LEAK],
            1,
            "validate-evidence-negative",
        ),
    ]
    for result_id, result_path, expected_exit, category in [
        ("valid", VALID_RESULT, 0, "report-positive"),
        ("missing-evidence", INVALID_MISSING_EVIDENCE, 1, "report-negative"),
        ("secret-leak", INVALID_SECRET_LEAK, 1, "report-negative"),
    ]:
        for fmt in ("text", "yaml", "json"):
            cases.append(
                _case(
                    f"report-{result_id}-{fmt}",
                    ["report", "--result", result_path, "--format", fmt],
                    expected_exit,
                    category,
                )
            )
    return cases


def run_evidence_matrix(
    cases: list[dict[str, Any]],
    *,
    framework_jar: Path,
    usage_kit_root: Path,
) -> dict[str, Any]:
    results = []
    for case in cases:
        argv = ["java", "-Xmx512m", "-jar", str(framework_jar), *case["command"]]
        proc = subprocess.run(
            argv,
            cwd=str(usage_kit_root),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        results.append(
            {
                **case,
                "argv": argv,
                "exit_code": proc.returncode,
                "stdout": redact_text(proc.stdout),
                "stderr": redact_text(proc.stderr),
                "status": _classify(case, proc.returncode, proc.stdout, proc.stderr),
            }
        )

    return {"summary": _summary(results), "results": results}


def write_evidence_matrix_report(report: dict[str, Any], output_dir: Path, *, version: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_version = version.removeprefix("v")
    json_path = output_dir / f"pi-run-v{clean_version}-evidence-command-matrix.json"
    markdown_path = output_dir / f"pi-run-v{clean_version}-evidence-command-matrix.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report, clean_version), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _case(case_id: str, command: list[str], expected_exit: int, category: str) -> dict[str, Any]:
    return {
        "id": case_id,
        "command": command,
        "expected_exit": expected_exit,
        "category": category,
    }


def _classify(case: dict[str, Any], exit_code: int, stdout: str, stderr: str) -> str:
    if "Unsupported --format: json" in stderr and "--format" in case["command"] and "json" in case["command"]:
        return "BLOCKED_FRAMEWORK_UNSUPPORTED_FORMAT"
    if case["expected_exit"] == 0:
        return "PASS" if exit_code == 0 else "FAIL"
    return "EXPECTED_FAIL" if exit_code != 0 else "FAIL"


def _summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "case_count": len(results),
        "pass_count": sum(1 for result in results if result["status"] == "PASS"),
        "expected_fail_count": sum(1 for result in results if result["status"] == "EXPECTED_FAIL"),
        "blocked_framework_count": sum(1 for result in results if result["status"].startswith("BLOCKED_FRAMEWORK_")),
        "unexpected_fail_count": sum(1 for result in results if result["status"] == "FAIL"),
        "report_supported_positive_status": _gate_status(
            results, "report-positive", "PASS", required_formats=SUPPORTED_REPORT_FORMATS
        ),
        "report_supported_positive_missing_formats": _missing_formats(results, "report-positive", SUPPORTED_REPORT_FORMATS),
        "report_supported_negative_status": _gate_status(
            results, "report-negative", "EXPECTED_FAIL", required_formats=SUPPORTED_REPORT_FORMATS
        ),
        "report_supported_negative_missing_formats": _missing_formats(results, "report-negative", SUPPORTED_REPORT_FORMATS),
        "validate_evidence_positive_status": _gate_status(results, "validate-evidence-positive", "PASS"),
        "validate_evidence_negative_status": _gate_status(results, "validate-evidence-negative", "EXPECTED_FAIL"),
    }


def _gate_status(
    results: list[dict[str, Any]],
    category: str,
    expected_status: str,
    *,
    required_formats: tuple[str, ...] = (),
) -> str:
    matching = [
        result
        for result in results
        if result["category"] == category and not result["status"].startswith("BLOCKED_FRAMEWORK_")
    ]
    if not matching:
        return "NOT_RUN"
    if required_formats and _missing_formats(results, category, required_formats):
        return "FAIL"
    if all(result["status"] == expected_status for result in matching):
        return expected_status
    return "FAIL"


def _missing_formats(results: list[dict[str, Any]], category: str, required_formats: tuple[str, ...]) -> list[str]:
    present = {
        fmt
        for result in results
        if result["category"] == category
        and not result["status"].startswith("BLOCKED_FRAMEWORK_")
        for fmt in [_command_format(result["command"])]
        if fmt
    }
    return [fmt for fmt in required_formats if fmt not in present]


def _command_format(command: list[str]) -> str | None:
    try:
        return command[command.index("--format") + 1]
    except (ValueError, IndexError):
        return None


def _markdown_report(report: dict[str, Any], version: str) -> str:
    summary = report["summary"]
    lines = [
        f"# pi-run v{version} Evidence Command Matrix",
        "",
        "## Summary",
        "",
        f"- Case count: `{summary['case_count']}`",
        f"- PASS: `{summary['pass_count']}`",
        f"- EXPECTED_FAIL: `{summary['expected_fail_count']}`",
        f"- BLOCKED_FRAMEWORK: `{summary['blocked_framework_count']}`",
        f"- Unexpected FAIL: `{summary['unexpected_fail_count']}`",
        f"- Report supported positive cases: `{summary['report_supported_positive_status']}`",
        f"- Report supported positive missing formats: `{', '.join(summary['report_supported_positive_missing_formats']) or 'none'}`",
        f"- Report supported negative cases: `{summary['report_supported_negative_status']}`",
        f"- Report supported negative missing formats: `{', '.join(summary['report_supported_negative_missing_formats']) or 'none'}`",
        f"- Validate-evidence positive cases: `{summary['validate_evidence_positive_status']}`",
        f"- Validate-evidence negative cases: `{summary['validate_evidence_negative_status']}`",
        "",
        "## Results",
        "",
        "| Case | Category | Expected Exit | Actual Exit | Status |",
        "|---|---|---:|---:|---:|",
    ]
    for result in report["results"]:
        lines.append(
            f"| `{result['id']}` | `{result['category']}` | {result['expected_exit']} | {result['exit_code']} | `{result['status']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-version", default="0.2.3")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    paths = framework_paths(args.framework_version)
    report = run_evidence_matrix(
        build_evidence_cases(),
        framework_jar=paths.jar,
        usage_kit_root=paths.usage_kit_root,
    )
    outputs = write_evidence_matrix_report(report, args.output_dir, version=args.framework_version)
    print(f"evidence_matrix_json: {outputs['json']}")
    print(f"evidence_matrix_markdown: {outputs['markdown']}")
    print(f"unexpected_fail_count: {report['summary']['unexpected_fail_count']}")
    print(f"blocked_framework_count: {report['summary']['blocked_framework_count']}")
    return 1 if report["summary"]["unexpected_fail_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
