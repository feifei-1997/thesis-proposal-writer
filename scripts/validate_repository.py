#!/usr/bin/env python3
"""Validate repository metadata, Skill frontmatter, and release safety."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HARDCODED_KEY_RE = re.compile(
    r"^\s*CQVIP_API_KEY\s*=\s*['\"](?P<value>[^'\"]+)['\"]",
    re.MULTILINE,
)
REQUIRED_FILES = (
    "SKILL.md",
    "README.md",
    "README.zh-CN.md",
    "LICENSE",
    "SECURITY.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "main.py",
    "runner.py",
    "_meta.json",
    "_skillhub_meta.json",
    "core/cqvip_client.py",
    "references/cqvip_api.md",
    "references/proposal_structure.md",
)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    lines = text.splitlines()
    if len(lines) < 4 or lines[0].strip() != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("SKILL.md frontmatter is not closed") from exc
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" in line:
            key, value = line.split(":", 1)
            values[key.strip()] = value.strip()
    return values


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            errors.append(f"missing required file: {relative}")

    try:
        frontmatter = parse_frontmatter(root / "SKILL.md")
        name = frontmatter.get("name", "")
        description = frontmatter.get("description", "")
        if not NAME_RE.fullmatch(name):
            errors.append("SKILL.md name must use lowercase letters, digits, and hyphens")
        if not description:
            errors.append("SKILL.md description is required")
    except (OSError, ValueError) as exc:
        errors.append(str(exc))
        frontmatter = {}

    try:
        public_meta = json.loads((root / "_meta.json").read_text(encoding="utf-8"))
        hub_meta = json.loads(
            (root / "_skillhub_meta.json").read_text(encoding="utf-8")
        )
        if public_meta.get("slug") != frontmatter.get("name"):
            errors.append("_meta.json slug must match SKILL.md name")
        if hub_meta.get("slug") != public_meta.get("slug"):
            errors.append("_skillhub_meta.json slug must match _meta.json")
        if hub_meta.get("version") != public_meta.get("version"):
            errors.append("metadata versions must match")
        if hub_meta.get("apiKeyEnv") != "CQVIP_API_KEY":
            errors.append("apiKeyEnv must be CQVIP_API_KEY")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"invalid metadata: {exc}")

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {
            ".py",
            ".json",
            ".yaml",
            ".yml",
            ".env",
        }:
            continue
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            continue
        match = HARDCODED_KEY_RE.search(text)
        if match and match.group("value").strip():
            errors.append(
                f"hardcoded CQVIP_API_KEY assignment found in {path.relative_to(root)}"
            )

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    root = args.root.resolve()
    errors = validate(root)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"Repository validation passed: {root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
