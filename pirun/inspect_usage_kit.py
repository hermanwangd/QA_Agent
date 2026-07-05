from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.framework_paths import framework_paths


REGISTRY_PATH = Path("docs/02-architecture/contracts/provider_capability_registry.v0.2.yaml")
CONTRACT_DIR = Path("docs/02-architecture/contracts/provider-contracts")
SAMPLES_DIR = Path("samples")
RELEASE_COMMANDS_PATH = Path("release/verification_commands.md")

REQUIRED_RELEASE_COMMANDS = ("validate", "run", "report", "validate-evidence")
CAPABILITY_ALIASES = {
    "compare": "artifact_compare",
    "polling": "polling_observer",
}
def inspect_usage_kit(usage_kit_root: Path) -> dict[str, Any]:
    usage_kit_root = usage_kit_root.resolve()
    registry = _read_yaml(usage_kit_root / REGISTRY_PATH)
    registry_providers = registry.get("provider_types", {})
    contracts = _load_contracts(usage_kit_root / CONTRACT_DIR)
    samples = _inspect_samples(usage_kit_root)
    release_commands = _release_commands(usage_kit_root / RELEASE_COMMANDS_PATH)

    rows: list[dict[str, Any]] = []
    for provider_type in sorted(registry_providers):
        entry = registry_providers[provider_type] or {}
        contract = contracts.get(provider_type, {})
        runtime_modes = _runtime_modes(entry, contract)
        contract_only_modes = set(entry.get("contract_only_runtime_modes") or contract.get("contract_only_runtime_modes") or [])
        runtime_status = _provider_runtime_status(entry, contract)
        for runtime_mode in runtime_modes:
            provider_samples = samples["by_provider_type_mode"].get(provider_type, {}).get(runtime_mode, set())
            indirect_samples = samples["by_capability_alias_mode"].get(provider_type, {}).get(runtime_mode, set())
            row = _matrix_row(
                provider_type=provider_type,
                runtime_mode=runtime_mode,
                runtime_modes=runtime_modes,
                runtime_status=runtime_status,
                contract_exists=provider_type in contracts,
                contract_only_modes=contract_only_modes,
                direct_sample_paths=provider_samples,
                indirect_sample_paths=indirect_samples,
                release_commands=release_commands,
            )
            rows.append(row)

    registry_without_contract = sorted(provider for provider in registry_providers if provider not in contracts)
    contracts_without_registry = sorted(provider for provider in contracts if provider not in registry_providers)
    present_release_commands = _present_release_commands(release_commands["commands"])
    missing_release_commands = sorted(set(REQUIRED_RELEASE_COMMANDS) - set(present_release_commands))

    rows.sort(key=lambda row: (row["provider_type"], row["runtime_mode"]))
    summary = {
        "usage_kit_root": str(usage_kit_root),
        "source_archive_used": False,
        "registry_provider_count": len(registry_providers),
        "contract_count": len(contracts),
        "matrix_row_count": len(rows),
        "registry_without_contract": registry_without_contract,
        "contracts_without_registry": contracts_without_registry,
        "present_release_verification_commands": present_release_commands,
        "missing_release_verification_commands": missing_release_commands,
        "sample_suite_count": samples["suite_count"],
        "sample_test_case_count": samples["test_case_count"],
    }
    return {"summary": summary, "matrix_rows": rows}


def write_matrix_reports(inspection: dict[str, Any], output_dir: Path, *, version: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_version = version.removeprefix("v")
    json_path = output_dir / f"pi-run-v{clean_version}-function-coverage-matrix.json"
    markdown_path = output_dir / f"pi-run-v{clean_version}-function-coverage-matrix.md"

    json_path.write_text(json.dumps(inspection, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_markdown_report(inspection, clean_version), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _matrix_row(
    *,
    provider_type: str,
    runtime_mode: str,
    runtime_modes: list[str],
    runtime_status: str | None,
    contract_exists: bool,
    contract_only_modes: set[str],
    direct_sample_paths: set[str],
    indirect_sample_paths: set[str],
    release_commands: dict[str, Any],
) -> dict[str, Any]:
    direct_sample = bool(direct_sample_paths)
    indirect_sample = bool(indirect_sample_paths)
    sample_paths = sorted(direct_sample_paths | indirect_sample_paths)

    expected_status = "PASS"
    runnable_now = True
    reason = "release usage-kit sample is present"
    resource_class = "lightweight"

    if not contract_exists:
        expected_status = "BLOCKED_CONTRACT_MISSING"
        runnable_now = False
        reason = "registry provider has no provider contract"
    elif runtime_status == "deprecated_alias":
        expected_status = "BLOCKED_DEPRECATED_ALIAS"
        runnable_now = False
        reason = "deprecated compatibility alias; new artifacts must use canonical provider type"
    elif runtime_status == "contract_only" or runtime_mode in contract_only_modes:
        expected_status = "BLOCKED_FRAMEWORK_CONTRACT_ONLY"
        runnable_now = False
        reason = f"{provider_type}/{runtime_mode} is contract-only in this framework release"
        resource_class = "heavy_or_external"
    elif not sample_paths:
        expected_status = "BLOCKED_USAGE_KIT_SAMPLE_GAP"
        runnable_now = False
        reason = "no direct or indirect usage-kit sample found for this provider"

    return {
        "provider_type": provider_type,
        "runtime_mode": runtime_mode,
        "runtime_modes": runtime_modes,
        "runtime_status": runtime_status,
        "contract_exists": contract_exists,
        "direct_sample": direct_sample,
        "indirect_sample": indirect_sample,
        "sample_paths": sample_paths,
        "release_verification_command": _matching_release_commands(sample_paths, release_commands),
        "runnable_now": runnable_now,
        "expected_status": expected_status,
        "owner": "project/pi-run" if runnable_now else "framework_or_project_gate",
        "resource_class": resource_class,
        "reason": reason,
    }


def _load_contracts(contract_dir: Path) -> dict[str, dict[str, Any]]:
    contracts: dict[str, dict[str, Any]] = {}
    for path in sorted(contract_dir.glob("*.yaml")):
        payload = _read_yaml(path)
        provider_type = payload.get("provider_type") or path.stem
        contracts[provider_type] = payload
    return contracts


def _inspect_samples(usage_kit_root: Path) -> dict[str, Any]:
    by_provider_type_mode: dict[str, dict[str, set[str]]] = {}
    by_capability_alias_mode: dict[str, dict[str, set[str]]] = {}
    suite_count = 0
    test_case_count = 0

    for suite_path in sorted((usage_kit_root / SAMPLES_DIR).rglob("suite_manifest.yaml")):
        suite_count += 1
        rel_suite = _rel(usage_kit_root, suite_path)
        suite_dir = suite_path.parent
        suite_runtime_modes: set[str] = set()
        capability_provider = CAPABILITY_ALIASES.get(suite_dir.name)

        for provider_instance_path in sorted((suite_dir / "provider_instances").glob("*.yaml")):
            provider_instance = _read_yaml(provider_instance_path)
            provider_type = provider_instance.get("provider_type")
            runtime_modes = provider_instance.get("runtime_modes") or []
            if provider_type:
                for runtime_mode in runtime_modes:
                    suite_runtime_modes.add(runtime_mode)
                    _add_sample(by_provider_type_mode, provider_type, runtime_mode, rel_suite)

        if capability_provider:
            for runtime_mode in suite_runtime_modes or {"stub"}:
                _add_sample(by_capability_alias_mode, capability_provider, runtime_mode, rel_suite)

        for test_case_path in sorted(suite_dir.glob("*test_case*.yaml")):
            test_case_count += 1
            test_case = _read_yaml(test_case_path)
            capability = ((test_case.get("labels") or {}).get("capability") or "").strip()
            provider_type = CAPABILITY_ALIASES.get(capability, capability)
            if provider_type:
                for runtime_mode in suite_runtime_modes or {"stub"}:
                    _add_sample(by_capability_alias_mode, provider_type, runtime_mode, rel_suite)

    return {
        "by_provider_type_mode": by_provider_type_mode,
        "by_capability_alias_mode": by_capability_alias_mode,
        "suite_count": suite_count,
        "test_case_count": test_case_count,
    }


def _add_sample(target: dict[str, dict[str, set[str]]], provider_type: str, runtime_mode: str, rel_suite: str) -> None:
    target.setdefault(provider_type, {}).setdefault(runtime_mode, set()).add(rel_suite)


def _runtime_modes(registry_entry: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    modes = []
    for key in ("supported_runtime_modes", "contract_runtime_modes"):
        modes.extend(registry_entry.get(key) or [])
    modes.extend(contract.get("runtime_modes") or [])
    modes.extend(registry_entry.get("contract_only_runtime_modes") or contract.get("contract_only_runtime_modes") or [])
    return sorted(dict.fromkeys(modes))


def _provider_runtime_status(registry_entry: dict[str, Any], contract: dict[str, Any]) -> str | None:
    if registry_entry.get("runtime_status"):
        return registry_entry["runtime_status"]
    if contract.get("status") == "deprecated_alias" or registry_entry.get("support_status") == "deprecated":
        return "deprecated_alias"
    return registry_entry.get("support_status") or contract.get("status")


def _release_commands(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    commands = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("java "):
            commands.append(stripped)
    return {"text": text, "commands": commands}


def _present_release_commands(commands: list[str]) -> list[str]:
    present = set()
    for command in commands:
        match = re.search(r"\.jar\s+([a-z-]+)\b", command)
        if match:
            present.add(match.group(1))
    return sorted(present)


def _matching_release_commands(sample_paths: list[str], release_commands: dict[str, Any]) -> list[str]:
    commands = []
    for command in release_commands["commands"]:
        if any(sample_path in command for sample_path in sample_paths):
            commands.append(command)
    if not commands and any(sample_path.startswith("samples/provider_capability/") for sample_path in sample_paths):
        for command in release_commands["commands"]:
            if "samples/provider_capability/suite_manifest.yaml" in command:
                commands.append(command)
    return commands


def _markdown_report(inspection: dict[str, Any], version: str) -> str:
    summary = inspection["summary"]
    lines = [
        f"# pi-run v{version} Function Coverage Matrix",
        "",
        "Generated from release usage-kit assets only.",
        "",
        "## Summary",
        "",
        f"- Source archive used: `{str(summary['source_archive_used']).lower()}`",
        f"- Registry provider count: `{summary['registry_provider_count']}`",
        f"- Provider contract count: `{summary['contract_count']}`",
        f"- Matrix row count: `{summary['matrix_row_count']}`",
        f"- Registry without contract: `{', '.join(summary['registry_without_contract']) or 'none'}`",
        f"- Contracts without registry: `{', '.join(summary['contracts_without_registry']) or 'none'}`",
        f"- Present release verification commands: `{', '.join(summary['present_release_verification_commands']) or 'none'}`",
        f"- Missing release verification commands: `{', '.join(summary['missing_release_verification_commands']) or 'none'}`",
        "",
        "## Matrix",
        "",
        "| Provider Type | Runtime Mode | Runtime Status | Contract | Direct Sample | Indirect Sample | Runnable | Expected Status | Reason |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in inspection["matrix_rows"]:
        lines.append(
            "| {provider_type} | {runtime_mode} | {runtime_status} | {contract_exists} | {direct_sample} | "
            "{indirect_sample} | {runnable_now} | {expected_status} | {reason} |".format(
                provider_type=f"`{row['provider_type']}`",
                runtime_mode=f"`{row['runtime_mode']}`",
                runtime_status=f"`{row['runtime_status']}`",
                contract_exists=_yes_no(row["contract_exists"]),
                direct_sample=_yes_no(row["direct_sample"]),
                indirect_sample=_yes_no(row["indirect_sample"]),
                runnable_now=_yes_no(row["runnable_now"]),
                expected_status=f"`{row['expected_status']}`",
                reason=row["reason"],
            )
        )
    lines.append("")
    return "\n".join(lines)


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _rel(root: Path, path: Path) -> str:
    return str(path.relative_to(root))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-version", default="0.2.3")
    parser.add_argument("--usage-kit-root", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    paths = framework_paths(args.framework_version)
    usage_kit_root = args.usage_kit_root or paths.usage_kit_root
    inspection = inspect_usage_kit(usage_kit_root)
    outputs = write_matrix_reports(inspection, args.output_dir, version=args.framework_version)
    print(f"matrix_json: {outputs['json']}")
    print(f"matrix_markdown: {outputs['markdown']}")
    print(f"matrix_row_count: {inspection['summary']['matrix_row_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
