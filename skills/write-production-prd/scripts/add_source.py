#!/usr/bin/env python3
"""Add a SRC-* evidence row to a PRD workspace."""

from __future__ import annotations

import argparse
import json
import re
import sys

from common import load_json, resolve_workspace, update_workspace_timestamp, write_json_atomic, write_text_atomic


def next_source_id(text: str) -> str:
    numbers = [int(value) for value in re.findall(r"\bSRC-(\d{3})\b", text)]
    return f"SRC-{max(numbers, default=0) + 1:03d}"


def add_source(workspace_arg: str, source_type: str, location: str, supports: str, confidence: str) -> dict[str, object]:
    if not source_type.strip() or not location.strip() or not supports.strip():
        raise ValueError("source type, location, and supports must not be empty")
    workspace = resolve_workspace(workspace_arg)
    notes_path = workspace / "inputs" / "source-notes.md"
    notes = notes_path.read_text(encoding="utf-8")
    source_id = next_source_id(notes)
    row = f"| {source_id} | {source_type.strip()} | {location.strip()} | {supports.strip()} | {confidence.strip()} | active |\n"
    lines = notes.splitlines(keepends=True)
    insert_at = 0
    for index, line in enumerate(lines):
        if line.startswith("| SRC-"):
            insert_at = index + 1
    if insert_at == 0:
        lines.append("\n## Evidence Ledger\n\n")
        lines.append("| ID | Type | Location | What it supports | Confidence | Status |\n")
        lines.append("|---|---|---|---|---|---|\n")
        insert_at = len(lines)
    lines.insert(insert_at, row)
    write_text_atomic(notes_path, "".join(lines))

    metadata_path = workspace / "workspace.json"
    metadata = load_json(metadata_path)
    evidence = list(metadata.get("evidence_index", []))
    if source_id not in evidence:
        evidence.append(source_id)
    metadata["evidence_index"] = evidence
    update_workspace_timestamp(metadata)
    write_json_atomic(metadata_path, metadata)
    return {"ok": True, "workspace": str(workspace), "source_id": source_id}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace")
    parser.add_argument("--type", required=True)
    parser.add_argument("--location", required=True)
    parser.add_argument("--supports", required=True)
    parser.add_argument("--confidence", default="medium", choices=["low", "medium", "high"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = add_source(args.workspace, args.type, args.location, args.supports, args.confidence)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else f"ADDED: {result['source_id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
