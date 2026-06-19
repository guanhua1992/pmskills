#!/usr/bin/env python3
"""Repository-local wrapper for the Codex Skill Creator validator."""

from __future__ import annotations

import re
import sys
from pathlib import Path


NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


def validate(skill: Path) -> list[str]:
    errors: list[str] = []
    skill_file = skill / "SKILL.md"
    if not skill_file.is_file():
        return [f"Missing {skill_file}"]
    text = skill_file.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return ["SKILL.md must start with YAML frontmatter"]
    frontmatter = match.group(1)
    fields = {}
    for line in frontmatter.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip()
    if set(fields) != {"name", "description"}:
        errors.append("Frontmatter must contain only name and description")
    name = fields.get("name", "")
    if not NAME_PATTERN.fullmatch(name):
        errors.append("Skill name must contain lowercase letters, digits, and hyphens only")
    if skill.name != name:
        errors.append("Skill directory name must match frontmatter name")
    if not fields.get("description"):
        errors.append("Skill description is required")
    if not (skill / "agents" / "openai.yaml").is_file():
        errors.append("Missing agents/openai.yaml")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: quick_validate.py <skill-directory>", file=sys.stderr)
        return 2
    errors = validate(Path(sys.argv[1]))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
