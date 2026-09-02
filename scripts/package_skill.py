#!/usr/bin/env python3
"""Build a deterministic, cross-platform Jenius Skill release archive."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from validate_repository import validate


ROOT_FILES = (
    "SKILL.md",
    "main.py",
    "runner.py",
    "_meta.json",
    "_skillhub_meta.json",
)
RESOURCE_DIRS = ("core", "references")
REQUIRED_ARCHIVE_ENTRIES = {
    "SKILL.md",
    "main.py",
    "runner.py",
    "_meta.json",
    "_skillhub_meta.json",
    "core/__init__.py",
    "core/cqvip_client.py",
    "references/cqvip_api.md",
    "references/proposal_structure.md",
}
FIXED_TIMESTAMP = (2020, 1, 1, 0, 0, 0)


def release_files(root: Path) -> list[Path]:
    files = [root / name for name in ROOT_FILES]
    for directory in RESOURCE_DIRS:
        files.extend(
            path
            for path in (root / directory).rglob("*")
            if path.is_file()
            and "__pycache__" not in path.parts
            and path.suffix not in {".pyc", ".pyo"}
        )
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def build_archive(root: Path, output_dir: Path, version: str, force: bool) -> Path:
    errors = validate(root)
    if errors:
        raise ValueError("repository validation failed:\n- " + "\n- ".join(errors))

    metadata = json.loads((root / "_meta.json").read_text(encoding="utf-8"))
    metadata_version = str(metadata.get("version") or "").strip()
    if version != metadata_version:
        raise ValueError(
            f"requested version {version!r} does not match metadata {metadata_version!r}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"thesis-proposal-writer-{version}.zip"
    hash_path = zip_path.with_suffix(zip_path.suffix + ".sha256")
    if not force and (zip_path.exists() or hash_path.exists()):
        raise FileExistsError(f"release artifact already exists: {zip_path}")

    with zipfile.ZipFile(zip_path, "w") as archive:
        for source in release_files(root):
            entry_name = source.relative_to(root).as_posix()
            if "\\" in entry_name or entry_name.startswith("/") or ".." in Path(entry_name).parts:
                raise ValueError(f"unsafe archive entry: {entry_name}")
            info = zipfile.ZipInfo(entry_name, FIXED_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, source.read_bytes())

    with zipfile.ZipFile(zip_path) as archive:
        names = set(archive.namelist())
        missing = REQUIRED_ARCHIVE_ENTRIES - names
        if missing:
            raise ValueError(f"archive is missing entries: {sorted(missing)}")
        if any("\\" in name for name in names):
            raise ValueError("archive contains Windows-style entry names")
        archive.testzip()

    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    hash_path.write_text(f"{digest}  {zip_path.name}\n", encoding="ascii")
    print(
        json.dumps(
            {
                "artifact": str(zip_path.resolve()),
                "sha256": digest,
                "hash_file": str(hash_path.resolve()),
            },
            ensure_ascii=False,
        )
    )
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    parser.add_argument("--output-dir", type=Path, default=Path("dist"))
    parser.add_argument("--version")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    metadata = json.loads((root / "_meta.json").read_text(encoding="utf-8"))
    version = args.version or str(metadata.get("version") or "").strip()
    if not version:
        print("ERROR: release version is empty", file=sys.stderr)
        return 1
    try:
        build_archive(root, args.output_dir.resolve(), version, args.force)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
