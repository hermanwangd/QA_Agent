from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.run_contract_baseline import REPO_ROOT
from pirun.redaction import SCAN_PATTERNS


TEXT_SUFFIXES = {".json", ".yaml", ".yml", ".md", ".txt", ".log"}
PATTERNS = SCAN_PATTERNS


def scan_paths(paths: list[Path]) -> dict[str, Any]:
    findings = []
    scanned_file_count = 0
    for root in paths:
        for path in _iter_text_files(root):
            scanned_file_count += 1
            text = _read_text(path)
            if text is None:
                continue
            for pattern_name, pattern in PATTERNS:
                for match in pattern.finditer(text):
                    findings.append(
                        {
                            "path": _display_path(path),
                            "pattern": pattern_name,
                            "line": text.count("\n", 0, match.start()) + 1,
                        }
                    )

    return {
        "raw_secret_scan": "FAIL" if findings else "PASS",
        "scanned_file_count": scanned_file_count,
        "findings": findings,
    }


def write_secret_scan_report(report: dict[str, Any], output_dir: Path, *, version: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_version = version.removeprefix("v")
    json_path = output_dir / f"pi-run-v{clean_version}-raw-secret-scan.json"
    markdown_path = output_dir / f"pi-run-v{clean_version}-raw-secret-scan.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report, clean_version), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _iter_text_files(root: Path):
    if root.is_file():
        candidates = [root]
    else:
        candidates = sorted(path for path in root.rglob("*") if path.is_file())
    for path in candidates:
        if path.suffix in TEXT_SUFFIXES:
            yield path


def _read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _markdown_report(report: dict[str, Any], version: str) -> str:
    lines = [
        f"# pi-run v{version} Raw Secret Scan",
        "",
        f"- Raw secret scan: `{report['raw_secret_scan']}`",
        f"- Scanned file count: `{report['scanned_file_count']}`",
        f"- Finding count: `{len(report['findings'])}`",
        "",
        "## Findings",
        "",
    ]
    if not report["findings"]:
        lines.append("No raw secret patterns found.")
    else:
        lines.extend(["| Path | Line | Pattern |", "|---|---:|---|"])
        for finding in report["findings"]:
            lines.append(f"| `{finding['path']}` | {finding['line']} | `{finding['pattern']}` |")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-version", default="0.2.3")
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv)

    paths = args.paths or [Path("reports"), Path(".pirun/runs")]
    report = scan_paths(paths)
    outputs = write_secret_scan_report(report, args.output_dir, version=args.framework_version)
    print(f"raw_secret_scan_json: {outputs['json']}")
    print(f"raw_secret_scan_markdown: {outputs['markdown']}")
    print(f"raw_secret_scan: {report['raw_secret_scan']}")
    print(f"finding_count: {len(report['findings'])}")
    return 0 if report["raw_secret_scan"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
