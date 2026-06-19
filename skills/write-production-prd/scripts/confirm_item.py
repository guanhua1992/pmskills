#!/usr/bin/env python3
"""Safely confirm a shaping stage, the module plan, a PRD module, or a review file."""

from __future__ import annotations

import argparse
import json
import re
import sys

from common import (
    BLOCKER_PATTERN,
    REVIEW_FILES,
    SHAPING_STAGES,
    VALID_DEPTHS,
    VALID_PROFILES,
    load_json,
    resolve_workspace,
    update_workspace_timestamp,
    write_json_atomic,
    write_text_atomic,
)


# kind -> status-marker word used in the `<!-- xxx-status: draft -->` comment.
STATUS_WORD = {"stage": "stage", "plan": "plan", "module": "module"}


def first_blocker(text: str) -> str | None:
    match = BLOCKER_PATTERN.search(text)
    return match.group(0) if match else None


def confirm(
    workspace_arg: str,
    kind: str,
    name: str | None,
    depth: str | None = None,
    product_profile: str | None = None,
) -> dict[str, object]:
    workspace = resolve_workspace(workspace_arg)
    metadata_path = workspace / "workspace.json"
    metadata = load_json(metadata_path)

    if kind == "stage":
        item = (name or "").removesuffix(".md")
        sequence = metadata.get("stage_sequence") or SHAPING_STAGES
        if item not in sequence:
            raise ValueError(f"Unknown stage: {name}")
        path = workspace / "shaping" / f"{item}.md"
        key = "confirmed_stages"
    elif kind == "module":
        item = (name or "").removesuffix(".md")
        if not item:
            raise ValueError("module confirmation requires --name")
        path = workspace / "prd" / "modules" / f"{item}.md"
        key = "confirmed_modules"
    elif kind == "plan":
        item = "module-plan"
        path = workspace / "prd" / "module-plan.md"
        key = None
    else:  # review
        item = (name or "").removesuffix(".md")
        if item not in REVIEW_FILES:
            raise ValueError(f"Unknown review file: {name}")
        path = workspace / "review" / f"{item}.md"
        key = None

    if not path.is_file():
        raise ValueError(f"Missing {kind}: {path}")
    text = path.read_text(encoding="utf-8")

    blocker = first_blocker(text)
    if blocker:
        raise ValueError(f"Cannot confirm {kind} with unresolved markers ({blocker}): {path}")

    if kind in STATUS_WORD:
        word = STATUS_WORD[kind]
        draft = f"{word}-status: draft"
        confirmed = f"{word}-status: confirmed"
        if draft not in text and confirmed not in text:
            raise ValueError(f"Cannot confirm {kind}: missing `{word}-status` marker in {path}")
        new_text = text.replace(draft, confirmed)
    else:  # review: clear any "Blocking decision [TO CONFIRM]" cell.
        # No hard requirement for the row — action-items.md is an aggregate table
        # without it. Unresolved markers are already caught by BLOCKER_PATTERN above.
        new_text = re.sub(
            r"(\| Blocking decision \|\s*)\[TO CONFIRM\](\s*\|)", r"\1no\2", text, flags=re.IGNORECASE
        )

    # Mutate (and for plan, validate) metadata BEFORE writing any file, so an
    # invalid confirmation raises without leaving a half-flipped status marker.
    if kind == "plan":
        new_depth = depth or metadata.get("depth")
        new_profile = product_profile or metadata.get("product_profile")
        if new_depth in (None, "auto") or new_profile in (None, "auto"):
            raise ValueError(
                "确认计划前必须确定具体 depth 与 product_profile（不能为 auto）；"
                "请用 --depth / --product-profile 指定"
            )
        if new_depth not in VALID_DEPTHS - {"auto"}:
            raise ValueError(f"Invalid depth: {new_depth}")
        if new_profile not in VALID_PROFILES - {"auto"}:
            raise ValueError(f"Invalid product_profile: {new_profile}")
        metadata["depth"] = new_depth
        metadata["product_profile"] = new_profile
    elif key:
        values = list(metadata.get(key, []))
        if item not in values:
            values.append(item)
        metadata[key] = values
    else:  # review
        review_status = dict(metadata.get("review_status", {}))
        review_status[item] = "confirmed"
        metadata["review_status"] = review_status

    if new_text != text:
        write_text_atomic(path, new_text)
    update_workspace_timestamp(metadata)
    write_json_atomic(metadata_path, metadata)
    result: dict[str, object] = {"ok": True, "workspace": str(workspace), "kind": kind, "name": item}
    if kind == "plan":
        result["depth"] = metadata["depth"]
        result["product_profile"] = metadata["product_profile"]
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace")
    parser.add_argument("--kind", required=True, choices=["stage", "plan", "module", "review"])
    parser.add_argument("--name", help="stage/module/review name (not needed for --kind plan)")
    parser.add_argument("--depth", choices=sorted(VALID_DEPTHS), help="for --kind plan: confirmed depth")
    parser.add_argument(
        "--product-profile", choices=sorted(VALID_PROFILES), help="for --kind plan: confirmed profile"
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = confirm(args.workspace, args.kind, args.name, args.depth, args.product_profile)
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False) if args.json else f"CONFIRMED: {args.kind} {result['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
