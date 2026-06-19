#!/usr/bin/env python3
"""Shared, dependency-free helpers for the production PRD skill."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


WORKSPACE_FILE = "workspace.json"
VALID_DEPTHS = {"auto", "brief", "standard", "enterprise"}
VALID_PROFILES = {"auto", "general", "b2b", "b2c", "ai-data"}
VALID_STATUSES = {"draft", "review-ready", "approved"}

# Unresolved-marker / placeholder pattern shared by the validator and the
# confirmation tool, so both block the same set before anything is confirmed.
BLOCKER_PATTERN = re.compile(
    r"\{\{[^}]+\}\}|\[TO CONFIRM\]|\[待确认\]|\[CONFLICT\]|\[冲突\]",
    re.IGNORECASE,
)
SHAPING_STAGES = [
    "00-discovery",
    "00-intake",
    "01-value-and-truth",
    "02-jtbd",
    "03-business-rules",
    "04-system-intent",
    "05-scope-and-version",
    "06-shaped-brief",
]
REVIEW_FILES = [
    "self-check",
    "version-review",
    "internal-review",
    "technical-review",
    "public-review",
    "action-items",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def slugify(value: str) -> str:
    value = value.strip().casefold()
    value = re.sub(r"[^\w-]+", "-", value, flags=re.UNICODE)
    value = re.sub(r"[-_]{2,}", "-", value).strip("-_")
    return value or "prd"


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    write_text_atomic(path, content)


def write_text_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def is_workspace(path: Path) -> bool:
    return path.is_dir() and (path / WORKSPACE_FILE).is_file()


def find_ancestor_workspace(start: Path) -> Path | None:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if is_workspace(candidate):
            return candidate
    return None


def _workspace_matches(path: Path, name: str) -> bool:
    try:
        data = load_json(path / WORKSPACE_FILE)
    except ValueError:
        return False
    return str(data.get("name", "")).casefold() == name.casefold()


def find_named_workspace(start: Path, name: str) -> Path | None:
    """Find a same-name workspace in current/parent/sibling scope."""
    start = start.resolve()
    ancestor = find_ancestor_workspace(start)
    if ancestor:
        return ancestor

    slug = slugify(name)
    search_roots: list[Path] = [start]
    if start.parent != start:
        search_roots.append(start.parent)

    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in search_roots:
        exact = root / f"{slug}-workspace"
        if is_workspace(exact) and _workspace_matches(exact, name):
            candidates.append(exact.resolve())
        if root.is_dir():
            for child in root.glob("*-workspace"):
                if is_workspace(child) and _workspace_matches(child, name):
                    candidates.append(child.resolve())

    unique = [path for path in candidates if not (path in seen or seen.add(path))]
    if len(unique) > 1:
        options = ", ".join(str(path) for path in unique)
        raise ValueError(f"Multiple matching workspaces found: {options}")
    return unique[0] if unique else None


def resolve_workspace(path: str | Path) -> Path:
    candidate = Path(path).expanduser().resolve()
    if is_workspace(candidate):
        return candidate
    ancestor = find_ancestor_workspace(candidate)
    if ancestor:
        return ancestor
    raise ValueError(f"No {WORKSPACE_FILE} found at or above {candidate}")


def render_tokens(text: str, tokens: dict[str, str]) -> str:
    for key, value in tokens.items():
        text = text.replace("{{" + key + "}}", value)
    return text


def update_workspace_timestamp(data: dict[str, Any]) -> None:
    data["updated_at"] = utc_now()
