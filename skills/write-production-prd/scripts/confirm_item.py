#!/usr/bin/env python3
"""Safely confirm a shaping stage, PRD module, or review file."""

from __future__ import annotations

import argparse
import json
import re
import sys

from common import REVIEW_FILES, SHAPING_STAGES, load_json, resolve_workspace, update_workspace_timestamp, write_json_atomic, write_text_atomic


def replace_marker(text: str, kind: str) -> str:
    if kind == "stage":
        return text.replace("stage-status: draft", "stage-status: confirmed")
    if kind == "module":
        return text.replace("module-status: draft", "module-status: confirmed")
    return re.sub(r"(\| Blocking decision \|\s*)\[TO CONFIRM\](\s*\|)", r"\1no\2", text, flags=re.IGNORECASE)


def confirm(workspace_arg: str, kind: str, name: str) -> dict[str, object]:
    workspace = resolve_workspace(workspace_arg)
    metadata_path = workspace / "workspace.json"
    metadata = load_json(metadata_path)
    if kind == "stage":
        item = name.removesuffix(".md")
        if item not in SHAPING_STAGES:
            raise ValueError(f"Unknown stage: {name}")
        path = workspace / "shaping" / f"{item}.md"
        key = "confirmed_stages"
    elif kind == "module":
        item = name.removesuffix(".md")
        path = workspace / "prd" / "modules" / f"{item}.md"
        key = "confirmed_modules"
    else:
        item = name.removesuffix(".md")
        if item not in REVIEW_FILES:
            raise ValueError(f"Unknown review file: {name}")
        path = workspace / "review" / f"{item}.md"
        key = None
    if not path.is_file():
        raise ValueError(f"Missing {kind}: {path}")
    text = path.read_text(encoding="utf-8")
    if "[TO CONFIRM]" in text or "[待确认]" in text:
        raise ValueError(f"Cannot confirm {kind} with unresolved markers: {path}")
    write_text_atomic(path, replace_marker(text, kind))

    if key:
        values = list(metadata.get(key, []))
        if item not in values:
            values.append(item)
        metadata[key] = values
    else:
        review_status = dict(metadata.get("review_status", {}))
        review_status[item] = "confirmed"
        metadata["review_status"] = review_status
    update_workspace_timestamp(metadata)
    write_json_atomic(metadata_path, metadata)
    return {"ok": True, "workspace": str(workspace), "kind": kind, "name": item}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace")
    parser.add_argument("--kind", required=True, choices=["stage", "module", "review"])
    parser.add_argument("--name", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = confirm(args.workspace, args.kind, args.name)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else f"CONFIRMED: {args.kind} {args.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
