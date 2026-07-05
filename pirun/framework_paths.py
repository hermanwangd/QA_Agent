from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FRAMEWORK_VERSION = "0.2.2"


@dataclass(frozen=True)
class FrameworkPaths:
    version: str
    release_asset_dir: Path
    jar: Path
    usage_kit_dir: Path
    usage_kit_root: Path
    samples_root: Path


def clean_framework_version(version: str) -> str:
    return version.removeprefix("v")


def release_asset_dir_for_version(version: str, *, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    clean_version = clean_framework_version(version)
    candidates = [
        root / "artifacts" / "release-assets" / f"release-assets-v{clean_version}",
        root / f"release-assets-v{clean_version}",
    ]
    if clean_version == "0.2.0":
        candidates.insert(1, root / "artifacts" / "release-assets" / "release-assets")
        candidates.append(root / "release-assets")
    return _first_existing(candidates)


def usage_kit_dir_for_version(version: str, *, repo_root: Path | None = None) -> Path:
    root = repo_root or REPO_ROOT
    clean_version = clean_framework_version(version)
    return _first_existing(
        [
            root / "artifacts" / "usage-kits" / f"usage-kit-v{clean_version}",
            root / f"usage-kit-v{clean_version}",
        ]
    )


def framework_paths(version: str, *, repo_root: Path | None = None) -> FrameworkPaths:
    clean_version = clean_framework_version(version)
    release_asset_dir = release_asset_dir_for_version(clean_version, repo_root=repo_root)
    usage_kit_dir = usage_kit_dir_for_version(clean_version, repo_root=repo_root)
    usage_kit_root = usage_kit_dir / "usage-kit"
    return FrameworkPaths(
        version=clean_version,
        release_asset_dir=release_asset_dir,
        jar=release_asset_dir / f"spec-driven-auto-regression-{clean_version}.jar",
        usage_kit_dir=usage_kit_dir,
        usage_kit_root=usage_kit_root,
        samples_root=usage_kit_root / "samples",
    )


def usage_kit_samples_root(
    version: str = DEFAULT_FRAMEWORK_VERSION,
    *,
    repo_root: Path | None = None,
) -> Path:
    return framework_paths(version, repo_root=repo_root).samples_root


def _first_existing(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]
