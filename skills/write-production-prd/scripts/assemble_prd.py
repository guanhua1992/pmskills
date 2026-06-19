#!/usr/bin/env python3
"""Safely assemble confirmed PRD modules into prd/PRD.md."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from common import (
    load_json,
    resolve_workspace,
    sha256_bytes,
    sha256_file,
    update_workspace_timestamp,
    utc_now,
    write_json_atomic,
    write_text_atomic,
)


def module_files(workspace: Path, confirmed_modules: list[str]) -> list[Path]:
    modules_dir = workspace / "prd" / "modules"
    files: list[Path] = []
    for module in confirmed_modules:
        name = module if module.endswith(".md") else f"{module}.md"
        path = modules_dir / name
        if not path.is_file():
            raise ValueError(f"Confirmed module is missing: {path}")
        text = path.read_text(encoding="utf-8")
        if "module-status: confirmed" not in text:
            raise ValueError(f"Confirmed module lacks confirmed status marker: {path}")
        files.append(path)
    return files


def assemble(workspace: Path) -> dict[str, object]:
    workspace_file = workspace / "workspace.json"
    data = load_json(workspace_file)
    confirmed = data.get("confirmed_modules", [])
    if not isinstance(confirmed, list) or not confirmed:
        raise ValueError("No confirmed modules recorded in workspace.json")

    prd_path = workspace / "prd" / "PRD.md"
    expected_hash = data.get("assembled_prd_sha256")
    if prd_path.exists():
        current_hash = sha256_file(prd_path)
        if expected_hash and current_hash != expected_hash:
            raise ValueError(
                "prd/PRD.md changed outside controlled assembly; resolve manual edits before assembling"
            )
        if not expected_hash and prd_path.read_text(encoding="utf-8").strip():
            raise ValueError(
                "prd/PRD.md has content but no trusted hash; refusing to overwrite"
            )

    files = module_files(workspace, [str(item) for item in confirmed])
    header = (
        "---\n"
        "artifact: prd\n"
        f'workspace: "{data.get("workspace_name", workspace.name)}"\n'
        f'depth: "{data.get("depth", "auto")}"\n'
        f'product_profile: "{data.get("product_profile", "auto")}"\n'
        f'status: "{data.get("status", "draft")}"\n'
        "generated_by: write-production-prd\n"
        "---\n\n"
        f'# PRD: {data.get("name", workspace.name)}\n\n'
        "<!-- Controlled output. Edit source modules, then reassemble. -->\n"
    )
    body_parts = [path.read_text(encoding="utf-8").strip() for path in files]
    content = header + "\n\n".join(body_parts) + "\n"
    new_hash = sha256_bytes(content.encode("utf-8"))

    write_text_atomic(prd_path, content)
    data["assembled_prd_sha256"] = new_hash
    data["assembled_module_hashes"] = {
        path.stem: sha256_file(path) for path in files
    }
    update_workspace_timestamp(data)
    write_json_atomic(workspace_file, data)

    log_path = workspace / "prd" / "_append-log.md"
    log = log_path.read_text(encoding="utf-8") if log_path.exists() else ""
    row = f"| {utc_now()} | `{new_hash}` | {', '.join(path.stem for path in files)} |\n"
    write_text_atomic(log_path, log + row)

    return {
        "ok": True,
        "workspace": str(workspace),
        "prd": str(prd_path),
        "sha256": new_hash,
        "modules": [path.stem for path in files],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", help="Workspace directory or a path inside it")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args()
    try:
        result = assemble(resolve_workspace(args.workspace))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else f"ASSEMBLED: {result['prd']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
