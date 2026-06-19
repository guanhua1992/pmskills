#!/usr/bin/env python3
"""Show current stage, module, review, and validation status for a PRD workspace."""

from __future__ import annotations

import argparse
import json
import sys

from common import REVIEW_FILES, SHAPING_STAGES, load_json, resolve_workspace
from validate_prd import validate


def status(workspace_arg: str) -> dict[str, object]:
    workspace = resolve_workspace(workspace_arg)
    metadata = load_json(workspace / "workspace.json")
    confirmed_stages = set(metadata.get("confirmed_stages", []))
    confirmed_modules = set(metadata.get("confirmed_modules", []))
    written_modules = sorted(path.stem for path in (workspace / "prd" / "modules").glob("*.md"))
    try:
        validation, _ = validate(workspace)
    except ValueError as exc:
        validation = {"ok": False, "score": 0, "blockers": [str(exc)]}
    sequence = metadata.get("stage_sequence") or SHAPING_STAGES
    next_stage = next((stage for stage in sequence if stage not in confirmed_stages), None)
    return {
        "ok": True,
        "workspace": str(workspace),
        "status": metadata.get("status", "draft"),
        "depth": metadata.get("depth", "auto"),
        "product_profile": metadata.get("product_profile", "auto"),
        "next_stage": next_stage,
        "confirmed_stages": sorted(confirmed_stages),
        "written_modules": written_modules,
        "confirmed_modules": sorted(confirmed_modules),
        "review_status": metadata.get("review_status", {name: "draft" for name in REVIEW_FILES}),
        "validation": validation,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = status(args.workspace)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Workspace: {result['workspace']}")
        print(f"Status: {result['status']} | Score: {result['validation']['score']}/100")
        print(f"Next stage: {result['next_stage'] or 'none'}")
        for blocker in result["validation"].get("blockers", []):
            print(f"- {blocker}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
