from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pirun.framework_paths import release_asset_dir_for_version

from pirun.run_contract_baseline import REPO_ROOT


SOURCE_ARCHIVE_NAMES = {
    "source.zip",
    "source.tar.gz",
    "v0.2.3.zip",
    "v0.2.3.tar.gz",
}


def verify_release_assets(asset_dir: Path) -> dict[str, Any]:
    asset_dir = asset_dir.resolve()
    checksum_path = asset_dir / "checksums.sha256"
    expected = _parse_checksums(checksum_path)
    assets = []

    for name, expected_sha256 in sorted(expected.items()):
        path = asset_dir / name
        actual_sha256 = _sha256(path) if path.exists() else None
        checksum_status = "PASS" if actual_sha256 == expected_sha256 else "MISSING" if not path.exists() else "FAIL"
        signature = _verify_signature(path) if path.exists() else {"status": "NOT_AVAILABLE", "reason": "asset_missing"}
        assets.append(
            {
                "name": name,
                "path": _display_path(path),
                "expected_sha256": expected_sha256,
                "actual_sha256": actual_sha256,
                "checksum_status": checksum_status,
                "signature_status": signature["status"],
                "signature_reason": signature.get("reason"),
                "certificate_subject": signature.get("certificate_subject"),
                "certificate_issuer": signature.get("certificate_issuer"),
            }
        )

    if checksum_path.exists() and "checksums.sha256" not in expected:
        signature = _verify_signature(checksum_path)
        assets.append(
            {
                "name": "checksums.sha256",
                "path": _display_path(checksum_path),
                "expected_sha256": None,
                "actual_sha256": _sha256(checksum_path),
                "checksum_status": "NOT_APPLICABLE",
                "signature_status": signature["status"],
                "signature_reason": signature.get("reason"),
                "certificate_subject": signature.get("certificate_subject"),
                "certificate_issuer": signature.get("certificate_issuer"),
            }
        )

    checksum_verification = "PASS" if assets and all(
        asset["checksum_status"] in {"PASS", "NOT_APPLICABLE"} for asset in assets
    ) else "FAIL"
    signature_statuses = [asset["signature_status"] for asset in assets]
    signature_verification = _aggregate_signature_status(signature_statuses)
    source_archive_indicators = sorted(path.name for path in asset_dir.iterdir() if _looks_like_source_archive(path.name))

    return {
        "release_asset_verification_version": "v0.1",
        "asset_dir": _display_path(asset_dir),
        "source_archive_used": bool(source_archive_indicators),
        "source_archive_indicators": source_archive_indicators,
        "checksum_verification": checksum_verification,
        "signature_verification": signature_verification,
        "signature_method": "openssl dgst -sha256 using release-provided certificate public key"
        if signature_verification == "PASS"
        else None,
        "certificate_chain_trust_verification": "NOT_PERFORMED" if signature_verification == "PASS" else None,
        "assets": assets,
    }


def write_release_asset_report(report: dict[str, Any], output_dir: Path, *, version: str) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    clean_version = version.removeprefix("v")
    json_path = output_dir / f"pi-run-v{clean_version}-release-asset-verification.json"
    markdown_path = output_dir / f"pi-run-v{clean_version}-release-asset-verification.md"

    json_path.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    markdown_path.write_text(_markdown_report(report, clean_version), encoding="utf-8")
    return {"json": json_path, "markdown": markdown_path}


def _parse_checksums(path: Path) -> dict[str, str]:
    checksums: dict[str, str] = {}
    if not path.exists():
        return checksums
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        checksum, raw_name = parts[0], parts[-1]
        checksums[Path(raw_name).name] = checksum
    return checksums


def _verify_signature(path: Path) -> dict[str, str]:
    sig_path = Path(f"{path}.sig")
    pem_path = Path(f"{path}.pem")
    if not sig_path.exists() or not pem_path.exists():
        return {"status": "NOT_AVAILABLE", "reason": "missing .sig or .pem"}

    try:
        cert_bytes = base64.b64decode(pem_path.read_bytes(), validate=True)
        sig_bytes = base64.b64decode(sig_path.read_bytes(), validate=True)
    except ValueError as exc:
        return {"status": "FAIL", "reason": f"base64 decode failed: {exc}"}

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        cert = tmp_dir / "cert.pem"
        sig = tmp_dir / "signature.der"
        pubkey = tmp_dir / "pubkey.pem"
        cert.write_bytes(cert_bytes)
        sig.write_bytes(sig_bytes)

        cert_info = _certificate_info(cert)
        pubkey_proc = subprocess.run(
            ["/usr/bin/openssl", "x509", "-in", str(cert), "-pubkey", "-noout"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if pubkey_proc.returncode != 0:
            return {"status": "FAIL", "reason": pubkey_proc.stderr.strip(), **cert_info}
        pubkey.write_text(pubkey_proc.stdout, encoding="utf-8")

        verify_proc = subprocess.run(
            [
                "/usr/bin/openssl",
                "dgst",
                "-sha256",
                "-verify",
                str(pubkey),
                "-signature",
                str(sig),
                str(path),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if verify_proc.returncode != 0:
            return {"status": "FAIL", "reason": verify_proc.stderr.strip() or verify_proc.stdout.strip(), **cert_info}
        return {"status": "PASS", "reason": verify_proc.stdout.strip(), **cert_info}


def _certificate_info(cert: Path) -> dict[str, str]:
    info = {}
    for key, option in (("certificate_subject", "-subject"), ("certificate_issuer", "-issuer")):
        proc = subprocess.run(
            ["/usr/bin/openssl", "x509", "-in", str(cert), "-noout", option],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if proc.returncode == 0:
            info[key] = proc.stdout.strip()
    return info


def _aggregate_signature_status(statuses: list[str]) -> str:
    if not statuses or all(status == "NOT_AVAILABLE" for status in statuses):
        return "NOT_AVAILABLE"
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if all(status == "PASS" for status in statuses):
        return "PASS"
    return "PARTIAL"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _looks_like_source_archive(name: str) -> bool:
    if name in SOURCE_ARCHIVE_NAMES:
        return True
    return name.startswith("Auto_Regression_Test_Framework-") and (name.endswith(".zip") or name.endswith(".tar.gz"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _markdown_report(report: dict[str, Any], version: str) -> str:
    lines = [
        f"# pi-run v{version} Release Asset Verification",
        "",
        f"- Source archive used: `{str(report['source_archive_used']).lower()}`",
        f"- Checksum verification: `{report['checksum_verification']}`",
        f"- Signature verification: `{report['signature_verification']}`",
    ]
    if report.get("signature_method"):
        lines.append(f"- Signature method: `{report['signature_method']}`")
    if report.get("certificate_chain_trust_verification"):
        lines.append(
            f"- Certificate chain trust verification: `{report['certificate_chain_trust_verification']}`"
        )
    lines.extend(
        [
            "",
            "## Assets",
            "",
            "| Asset | Checksum | Signature |",
            "|---|---:|---:|",
        ]
    )
    for asset in report["assets"]:
        lines.append(
            f"| `{asset['name']}` | `{asset['checksum_status']}` | `{asset['signature_status']}` |"
        )
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--framework-version", default="0.2.3")
    parser.add_argument("--asset-dir", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args(argv)

    clean_version = args.framework_version.removeprefix("v")
    asset_dir = args.asset_dir or release_asset_dir_for_version(clean_version, repo_root=REPO_ROOT)
    report = verify_release_assets(asset_dir)
    outputs = write_release_asset_report(report, args.output_dir, version=clean_version)
    print(f"release_asset_report_json: {outputs['json']}")
    print(f"release_asset_report_markdown: {outputs['markdown']}")
    print(f"checksum_verification: {report['checksum_verification']}")
    print(f"signature_verification: {report['signature_verification']}")
    return 0 if report["checksum_verification"] == "PASS" and report["signature_verification"] in {"PASS", "NOT_AVAILABLE"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
