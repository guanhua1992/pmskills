#!/usr/bin/env python3
"""Initialize or resume a production PRD workspace."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

from common import (
    REVIEW_FILES,
    SHAPING_STAGES,
    VALID_DEPTHS,
    VALID_PROFILES,
    find_named_workspace,
    render_tokens,
    sha256_file,
    slugify,
    utc_now,
    write_json_atomic,
)


SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
TEMPLATE_DIR = SKILL_DIR / "assets" / "workspace-template"


def copy_template(template: Path, target: Path, tokens: dict[str, str]) -> None:
    for source in template.rglob("*"):
        relative = source.relative_to(template)
        if source.name == ".DS_Store":
            continue
        destination = target / relative
        if source.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Binary asset (image, etc.): copy verbatim, no token rendering.
            destination.write_bytes(source.read_bytes())
            continue
        destination.write_text(render_tokens(text, tokens), encoding="utf-8")


def initialize(
    name: str,
    root: Path,
    depth: str,
    profile: str,
    output_language: str = "zh-CN",
) -> tuple[Path, bool]:
    existing = find_named_workspace(root, name)
    if existing:
        return existing, False

    root = root.resolve()
    root.mkdir(parents=True, exist_ok=True)
    workspace = root / f"{slugify(name)}-workspace"
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError(
            f"Refusing to initialize non-empty directory without workspace.json: {workspace}"
        )
    if workspace.exists():
        workspace.rmdir()

    temporary = root / f".{workspace.name}.init-{os.getpid()}"
    if temporary.exists():
        raise ValueError(f"Temporary initialization directory already exists: {temporary}")

    tokens = {
        "PRODUCT_NAME": name,
        "WORKSPACE_NAME": workspace.name,
        "DEPTH": depth,
        "PRODUCT_PROFILE": profile,
    }
    try:
        temporary.mkdir()
        copy_template(TEMPLATE_DIR, temporary, tokens)
        (temporary / "prd" / "modules").mkdir(parents=True, exist_ok=True)

        now = utc_now()
        prd_path = temporary / "prd" / "PRD.md"
        metadata = {
            "version": 2,
            "name": name,
            "workspace_name": workspace.name,
            "depth": depth,
            "product_profile": profile,
            "output_language": output_language,
            "status": "draft",
            "current_stage": "00-discovery",
            "confirmed_stages": [],
            "confirmed_modules": [],
            "review_status": {name: "draft" for name in REVIEW_FILES},
            "stage_sequence": SHAPING_STAGES,
            "evidence_index": ["SRC-001"],
            "assembled_prd_sha256": sha256_file(prd_path),
            "assembled_module_hashes": {},
            "created_at": now,
            "updated_at": now,
        }
        write_json_atomic(temporary / "workspace.json", metadata)
        temporary.replace(workspace)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise
    return workspace, True


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True, help="Product or feature name")
    parser.add_argument(
        "--depth", default="auto", choices=sorted(VALID_DEPTHS), help="PRD depth"
    )
    parser.add_argument(
        "--product-profile",
        default="auto",
        choices=sorted(VALID_PROFILES),
        help="Product profile",
    )
    parser.add_argument(
        "--root", default=".", help="Directory in which to find or create the workspace"
    )
    parser.add_argument(
        "--output-language",
        default="zh-CN",
        help="Default narrative language for the PRD (e.g. zh-CN, en, follow-user)",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        workspace, created = initialize(
            args.name,
            Path(args.root).expanduser(),
            args.depth,
            args.product_profile,
            args.output_language,
        )
    except (OSError, ValueError, shutil.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    result = {
        "ok": True,
        "created": created,
        "action": "created" if created else "resumed",
        "workspace": str(workspace),
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{result['action'].upper()}: {workspace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
