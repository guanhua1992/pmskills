#!/usr/bin/env python3
"""Validate PRD structure, traceability, requirement quality, and promotion gates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from common import (
    BLOCKER_PATTERN,
    REVIEW_FILES,
    SHAPING_STAGES,
    VALID_STATUSES,
    load_json,
    resolve_workspace,
    sha256_file,
    update_workspace_timestamp,
    write_json_atomic,
    write_text_atomic,
)


SECTION_MARKERS = [
    "PRD-CONTROL",
    "PRD-BACKGROUND",
    "PRD-GOALS",
    "PRD-USERS",
    "PRD-SCOPE",
    "PRD-FLOWS",
    "PRD-REQUIREMENTS",
    "PRD-RULES",
    "PRD-EXCEPTIONS",
    "PRD-DATA",
    "PRD-PERMISSIONS",
    "PRD-INTEGRATIONS",
    "PRD-NFR",
    "PRD-METRICS",
    "PRD-RELEASE",
    "PRD-ACCEPTANCE",
    "PRD-RISKS",
    "PRD-VIBE-SPEC",
    "PRD-TRACEABILITY",
]
VAGUE_PATTERN = re.compile(
    r"\b(fast|easy|intuitive|appropriate|generally|timely|user-friendly|"
    r"quickly|efficient|seamless|as soon as possible)\b|"
    r"(尽快|友好|合理|适当|快速|高效|及时|简单易用)",
    re.IGNORECASE,
)
ID_PATTERNS = {
    "FR": re.compile(r"\bFR-\d{3}\b"),
    "NFR": re.compile(r"\bNFR-\d{3}\b"),
    "AC": re.compile(r"\bAC-\d{3}\b"),
}
SOURCE_PATTERN = re.compile(r"\bSRC-\d{3}\b")
PROFILE_TERMS = {
    "general": {
        "Platform or compatibility": r"Platform|平台|Compatibility|兼容",
        "Support or operations impact": r"Support|支持|Operations|运营|运维",
    },
    "b2b": {
        "Permission Matrix": r"Permission Matrix|权限矩阵",
        "Approval or status workflow": r"Approval|审批|Status|状态",
        "Audit coverage": r"Audit|审计",
        "Data scope or tenant boundary": r"Data Scope|数据范围|Tenant|租户",
    },
    "b2c": {
        "Funnel or conversion metric": r"Funnel|漏斗|Conversion|转化",
        "Privacy or consent": r"Privacy|隐私|Consent|同意|授权",
        "Empty state and recovery": r"Empty State|空状态|Recovery|恢复",
        "Compatibility target": r"Compatibility|兼容|Device|设备|Browser|浏览器|Platform|平台",
        "Risk or abuse handling": r"Abuse|滥用|Risk|风险|Fraud|欺诈|Safety|安全",
    },
    "ai-data": {
        "Evaluation method or dataset": r"Evaluation|评估|Dataset|数据集",
        "Confidence or threshold": r"Confidence|置信|Threshold|阈值",
        "Human fallback or review": r"Human Review|人工审核|Fallback|兜底",
        "Monitoring or quality alert": r"Monitoring|监控|Alert|告警|Drift|漂移",
        "Cost and latency": r"Cost|成本|Latency|延迟",
        "Lineage or freshness": r"Lineage|血缘|Freshness|新鲜度|Source Quality|来源质量",
    },
}


@dataclass
class Check:
    name: str
    points: int
    earned: int
    detail: str
    blocker: bool = False


def section_block(text: str, marker: str) -> str:
    match = re.search(rf"^##+ .*?\[{re.escape(marker)}\].*$", text, re.MULTILINE)
    if not match:
        return ""
    start = match.start()
    next_match = re.search(r"^##+ .*?\[PRD-[A-Z-]+\].*$", text[match.end() :], re.MULTILINE)
    end = match.end() + next_match.start() if next_match else len(text)
    return text[start:end]


def defined_ids(text: str, kind: str) -> tuple[list[str], list[str]]:
    if kind in {"FR", "NFR"}:
        ids = re.findall(rf"^### ({kind}-\d{{3}})\s*[:：]", text, re.MULTILINE)
    else:
        ids = re.findall(r"^\s*-\s*(AC-\d{3})\s*[:：]", text, re.MULTILINE)
    duplicates = sorted({value for value in ids if ids.count(value) > 1})
    return ids, duplicates


def requirement_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^### (FR-\d{3})\s*[:：].*$", text, re.MULTILINE))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.start() : end]))
    return blocks


def nfr_blocks(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^### (NFR-\d{3})\s*[:：].*$", text, re.MULTILINE))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        blocks.append((match.group(1), text[match.start() : end]))
    return blocks


def extract_source_ids(source_notes: str) -> set[str]:
    return set(SOURCE_PATTERN.findall(source_notes))


def strip_table_separator(line: str) -> bool:
    return bool(re.fullmatch(r"\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*", line))


def definition_ids(text: str, prefix: str) -> set[str]:
    return set(
        re.findall(
            rf"^(?:\s*-\s*|\s*\|\s*)({prefix}-\d{{3}})\b",
            text,
            re.MULTILINE,
        )
    )


def validate(workspace: Path) -> tuple[dict[str, object], list[Check]]:
    metadata = load_json(workspace / "workspace.json")
    prd_path = workspace / "prd" / "PRD.md"
    if not prd_path.is_file():
        raise ValueError(f"Missing PRD: {prd_path}")
    text = prd_path.read_text(encoding="utf-8")
    source_notes = (workspace / "inputs" / "source-notes.md").read_text(encoding="utf-8")
    checks: list[Check] = []

    # Validate each workspace against the stage sequence snapshotted at init,
    # falling back to the current default. This keeps v1 workspaces (without the
    # discovery stage) valid after the sequence is extended.
    sequence = metadata.get("stage_sequence") or SHAPING_STAGES
    confirmed_stages = {str(value).removesuffix(".md") for value in metadata.get("confirmed_stages", [])}
    stage_files = [workspace / "shaping" / f"{stage}.md" for stage in sequence]
    stage_markers_ok = all(
        path.is_file() and "stage-status: confirmed" in path.read_text(encoding="utf-8")
        for path in stage_files
    )
    stages_ok = confirmed_stages == set(sequence) and stage_markers_ok
    checks.append(
        Check(
            "All shaping stages confirmed",
            0,
            0,
            f"{len(confirmed_stages)}/{len(sequence)} stages confirmed",
            blocker=not stages_ok,
        )
    )

    review_files = [workspace / "review" / f"{name}.md" for name in REVIEW_FILES]
    review_text = "\n".join(path.read_text(encoding="utf-8") for path in review_files if path.is_file())
    review_missing = [str(path.relative_to(workspace)) for path in review_files if not path.is_file()]
    review_unresolved = sorted(set(BLOCKER_PATTERN.findall(review_text)))
    blocking_review_rows = []
    for line in review_text.splitlines():
        if strip_table_separator(line):
            continue
        normalized = line.casefold()
        if "| yes | open |" in normalized or "| yes | [to confirm]" in normalized:
            blocking_review_rows.append(line.strip())
        if "blocking decision" in normalized and ("[to confirm]" in normalized or "yes" in normalized or "是" in line):
            blocking_review_rows.append(line.strip())
    review_blockers = review_missing + review_unresolved + blocking_review_rows
    checks.append(
        Check(
            "Review package is non-blocking",
            5,
            5 if not review_blockers else 0,
            "Review package ready"
            if not review_blockers
            else f"Review blockers: {', '.join(review_blockers[:3])}",
            blocker=bool(review_blockers),
        )
    )

    analysis_text = source_notes + "\n" + "\n".join(
        path.read_text(encoding="utf-8") for path in stage_files if path.is_file()
    )
    analysis_unresolved = sorted(set(BLOCKER_PATTERN.findall(analysis_text)))
    checks.append(
        Check(
            "No unresolved analysis-chain markers",
            0,
            0,
            "Clean"
            if not analysis_unresolved
            else f"Found unresolved analysis markers: {', '.join(analysis_unresolved[:5])}",
            blocker=bool(analysis_unresolved),
        )
    )

    missing_sections = [marker for marker in SECTION_MARKERS if f"[{marker}]" not in text]
    section_earned = round(20 * (len(SECTION_MARKERS) - len(missing_sections)) / len(SECTION_MARKERS))
    checks.append(
        Check(
            "Required PRD structure",
            20,
            section_earned,
            "Complete" if not missing_sections else f"Missing: {', '.join(missing_sections)}",
            blocker=bool(missing_sections),
        )
    )

    unresolved = sorted(set(BLOCKER_PATTERN.findall(text)))
    checks.append(
        Check(
            "No unresolved blockers or placeholders",
            0,
            0,
            "Clean" if not unresolved else f"Found unresolved markers: {', '.join(unresolved[:5])}",
            blocker=bool(unresolved),
        )
    )

    all_ids: dict[str, list[str]] = {}
    duplicate_ids: list[str] = []
    for kind in ID_PATTERNS:
        ids, duplicates = defined_ids(text, kind)
        all_ids[kind] = ids
        duplicate_ids.extend(duplicates)
    checks.append(
        Check(
            "Stable IDs are unique",
            5,
            5 if not duplicate_ids else 0,
            "Unique" if not duplicate_ids else f"Duplicates: {', '.join(duplicate_ids)}",
            blocker=bool(duplicate_ids),
        )
    )

    requirements = requirement_blocks(section_block(text, "PRD-REQUIREMENTS"))
    bad_requirements: list[str] = []
    referenced_sources: set[str] = set()
    referenced_acceptance: set[str] = set()
    defined_goals = definition_ids(text, "GOAL")
    defined_scenarios = definition_ids(text, "SCN")
    defined_rules = definition_ids(text, "BR")
    traceability = section_block(text, "PRD-TRACEABILITY")
    for requirement_id, block in requirements:
        has_priority = bool(re.search(r"^-\s*(Priority|优先级)\s*[:：]", block, re.MULTILINE))
        traces = re.search(r"^-\s*(Traces To|追踪至)\s*[:：](.*)$", block, re.MULTILINE)
        trace_text = traces.group(2) if traces else ""
        goal_refs = set(re.findall(r"\bGOAL-\d{3}\b", trace_text))
        scenario_refs = set(re.findall(r"\bSCN-\d{3}\b", trace_text))
        source_refs = set(SOURCE_PATTERN.findall(trace_text))
        has_trace = (
            bool(goal_refs)
            and bool(scenario_refs)
            and bool(source_refs)
            and goal_refs <= defined_goals
            and scenario_refs <= defined_scenarios
        )
        rule_line = re.search(r"^-\s*(Business Rules|业务规则)\s*[:：](.*)$", block, re.MULTILINE)
        rule_refs = set(re.findall(r"\bBR-\d{3}\b", rule_line.group(2) if rule_line else ""))
        has_rules = bool(rule_refs) and rule_refs <= defined_rules
        ac_ids = set(ID_PATTERNS["AC"].findall(block))
        ac_lines = re.findall(r"^\s*-\s*AC-\d{3}\s*[:：](.*)$", block, re.MULTILINE)
        testable_ac = bool(ac_lines) and all(
            (
                all(token in line.casefold() for token in ("given", "when", "then"))
                or all(token in line for token in ("假设", "当", "则"))
            )
            for line in ac_lines
        )
        referenced_acceptance.update(ac_ids)
        referenced_sources.update(SOURCE_PATTERN.findall(block))
        vague = bool(VAGUE_PATTERN.search(block))
        in_traceability = requirement_id in traceability
        if not (
            has_priority
            and has_trace
            and has_rules
            and ac_ids
            and testable_ac
            and in_traceability
        ) or vague:
            bad_requirements.append(requirement_id)
    req_score = 25
    if not requirements:
        req_score = 0
    elif bad_requirements:
        req_score = max(0, round(25 * (len(requirements) - len(bad_requirements)) / len(requirements)))
    checks.append(
        Check(
            "Functional requirements are testable and traceable",
            25,
            req_score,
            f"{len(requirements)} requirements checked"
            if not bad_requirements
            else f"Needs work: {', '.join(bad_requirements)}",
            blocker=not requirements or bool(bad_requirements),
        )
    )

    orphan_acceptance = sorted(set(all_ids["AC"]) - referenced_acceptance)
    checks.append(
        Check(
            "Acceptance IDs belong to functional requirements",
            5,
            5 if not orphan_acceptance else 0,
            "Connected" if not orphan_acceptance else f"Orphans: {', '.join(orphan_acceptance)}",
            blocker=bool(orphan_acceptance),
        )
    )

    known_sources = extract_source_ids(source_notes)
    referenced_sources.update(SOURCE_PATTERN.findall(text))
    missing_sources = sorted(referenced_sources - known_sources)
    checks.append(
        Check(
            "Evidence references resolve",
            10,
            10 if not missing_sources else 0,
            "Resolved" if not missing_sources else f"Missing evidence: {', '.join(missing_sources)}",
            blocker=bool(missing_sources),
        )
    )

    nfrs = nfr_blocks(section_block(text, "PRD-NFR"))
    bad_nfrs: list[str] = []
    measurable = re.compile(r"\d+(?:\.\d+)?\s*(?:ms|s|sec|seconds?|minutes?|%|rps|requests?/second|MB|GB|次|秒|分钟)")
    not_applicable = re.compile(r"(Not applicable because|不适用，因为|不适用:|不适用：)", re.IGNORECASE)
    for nfr_id, block in nfrs:
        if not (measurable.search(block) or not_applicable.search(block)):
            bad_nfrs.append(nfr_id)
    checks.append(
        Check(
            "NFRs are measurable or explicitly not applicable",
            10,
            10 if nfrs and not bad_nfrs else 0,
            f"{len(nfrs)} NFRs checked" if not bad_nfrs else f"Needs targets: {', '.join(bad_nfrs)}",
            blocker=not nfrs or bool(bad_nfrs),
        )
    )

    coverage_markers = [
        "PRD-FLOWS",
        "PRD-EXCEPTIONS",
        "PRD-DATA",
        "PRD-PERMISSIONS",
        "PRD-INTEGRATIONS",
    ]
    coverage = sum(bool(section_block(text, marker).strip()) for marker in coverage_markers)
    checks.append(
        Check(
            "Flow and operational coverage",
            10,
            round(10 * coverage / len(coverage_markers)),
            f"{coverage}/{len(coverage_markers)} coverage areas present",
        )
    )

    delivery_markers = [
        "PRD-METRICS",
        "PRD-RELEASE",
        "PRD-ACCEPTANCE",
        "PRD-RISKS",
        "PRD-TRACEABILITY",
    ]
    delivery = sum(bool(section_block(text, marker).strip()) for marker in delivery_markers)
    checks.append(
        Check(
            "Delivery and decision coverage",
            10,
            round(10 * delivery / len(delivery_markers)),
            f"{delivery}/{len(delivery_markers)} coverage areas present",
        )
    )

    vibe_block = section_block(text, "PRD-VIBE-SPEC")
    vibe_requirements = {
        "Build intent": r"Build intent|构建意图|产品能力",
        "Users": r"Users|用户",
        "Modules": r"Modules|模块",
        "Inputs": r"Inputs|输入",
        "Outputs": r"Outputs|输出",
        "Boundaries": r"Boundaries|边界",
        "Done criteria": r"Done criteria|完成标准",
        "AI non-decisions": r"AI non-decisions|AI 不得决策|禁止.*自行决定",
    }
    missing_vibe = [
        name
        for name, pattern in vibe_requirements.items()
        if not re.search(pattern, vibe_block, re.IGNORECASE)
    ]
    checks.append(
        Check(
            "Vibe Coding intent is complete",
            5,
            5 if vibe_block and not missing_vibe else 0,
            "Complete" if vibe_block and not missing_vibe else f"Missing: {', '.join(missing_vibe)}",
            blocker=not vibe_block or bool(missing_vibe),
        )
    )

    profile = str(metadata.get("product_profile", "auto"))
    if profile == "auto":
        checks.append(
            Check(
                "Product profile gates",
                5,
                0,
                "product_profile 仍为 auto；请在模块计划确认后落定具体画像 "
                "(general/b2b/b2c/ai-data)",
                blocker=True,
            )
        )
    else:
        profile_terms = PROFILE_TERMS.get(profile, {})
        missing_profile = [
            name
            for name, pattern in profile_terms.items()
            if not re.search(pattern, text, re.IGNORECASE)
        ]
        checks.append(
            Check(
                "Product profile gates",
                5,
                5 if not missing_profile else 0,
                "No profile-specific blockers"
                if not missing_profile
                else f"Missing {profile} coverage: {', '.join(missing_profile)}",
                blocker=bool(missing_profile),
            )
        )

    expected_hash = metadata.get("assembled_prd_sha256")
    current_hash = sha256_file(prd_path)
    hash_ok = not expected_hash or current_hash == expected_hash
    checks.append(
        Check(
            "Controlled assembly hash",
            2,
            2 if hash_ok else 0,
            "Trusted" if hash_ok else "PRD changed outside controlled assembly",
            blocker=not hash_ok,
        )
    )

    confirmed = {str(value).removesuffix(".md") for value in metadata.get("confirmed_modules", [])}
    written = {path.stem for path in (workspace / "prd" / "modules").glob("*.md")}
    status_confirmed = all(
        "module-status: confirmed" in (workspace / "prd" / "modules" / f"{name}.md").read_text(encoding="utf-8")
        for name in confirmed
        if (workspace / "prd" / "modules" / f"{name}.md").is_file()
    )
    all_modules_confirmed = bool(written) and written == confirmed and status_confirmed
    checks.append(
        Check(
            "All written modules confirmed",
            3,
            3 if all_modules_confirmed else 0,
            f"{len(confirmed)}/{len(written)} modules confirmed",
            blocker=not all_modules_confirmed,
        )
    )

    raw_score = sum(check.earned for check in checks)
    max_score = sum(check.points for check in checks)
    score = round(raw_score * 100 / max_score) if max_score else 0
    blockers = [check.detail for check in checks if check.blocker]
    result = {
        "ok": not blockers and score >= 85,
        "score": score,
        "raw_score": raw_score,
        "max_score": max_score,
        "threshold": 85,
        "status": metadata.get("status", "draft"),
        "blockers": blockers,
        "checks": [
            {
                "name": check.name,
                "points": check.points,
                "earned": check.earned,
                "detail": check.detail,
                "blocker": check.blocker,
            }
            for check in checks
        ],
    }
    return result, checks


def render_report(result: dict[str, object]) -> str:
    rows = [
        "# PRD Quality Report",
        "",
        f"- Score: **{result['score']}/100**",
        f"- Raw score: **{result['raw_score']}/{result['max_score']}**",
        f"- Threshold: **{result['threshold']}**",
        f"- Result: **{'PASS' if result['ok'] else 'FAIL'}**",
        f"- Status: **{result['status']}**",
        "",
        "## Checks",
        "",
        "| Check | Earned | Available | Blocker | Detail |",
        "|---|---:|---:|---|---|",
    ]
    for check in result["checks"]:
        rows.append(
            f"| {check['name']} | {check['earned']} | {check['points']} | "
            f"{'yes' if check['blocker'] else 'no'} | {check['detail']} |"
        )
    rows.extend(["", "## Blockers", ""])
    blockers = result["blockers"]
    rows.extend([f"- {item}" for item in blockers] if blockers else ["- None"])
    return "\n".join(rows) + "\n"


def promote(workspace: Path, result: dict[str, object], new_status: str) -> None:
    if not result["ok"]:
        raise ValueError("Cannot promote a PRD that does not pass the quality gate")
    metadata_path = workspace / "workspace.json"
    metadata = load_json(metadata_path)
    current = metadata.get("status", "draft")
    allowed = {("draft", "review-ready"), ("review-ready", "approved")}
    if (current, new_status) not in allowed:
        raise ValueError(f"Invalid status transition: {current} -> {new_status}")

    prd_path = workspace / "prd" / "PRD.md"
    expected_hash = metadata.get("assembled_prd_sha256")
    if expected_hash and sha256_file(prd_path) != expected_hash:
        raise ValueError("Cannot promote a PRD with an assembly hash conflict")
    prd_text = prd_path.read_text(encoding="utf-8")
    updated_prd = re.sub(
        r'^status:\s*["\']?[^"\']+["\']?\s*$',
        f'status: "{new_status}"',
        prd_text,
        count=1,
        flags=re.MULTILINE,
    )
    if updated_prd == prd_text:
        raise ValueError("Cannot promote because PRD frontmatter status is missing")
    write_text_atomic(prd_path, updated_prd)
    metadata["status"] = new_status
    metadata["assembled_prd_sha256"] = sha256_file(prd_path)
    update_workspace_timestamp(metadata)
    write_json_atomic(metadata_path, metadata)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", help="Workspace directory or a path inside it")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on gate failure")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    parser.add_argument("--set-status", choices=sorted(VALID_STATUSES - {"draft"}))
    args = parser.parse_args()

    try:
        workspace = resolve_workspace(args.workspace)
        result, _ = validate(workspace)
        if args.set_status:
            promote(workspace, result, args.set_status)
            result["status"] = args.set_status
        write_text_atomic(workspace / "prd" / "quality-report.md", render_report(result))
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"{'PASS' if result['ok'] else 'FAIL'}: {result['score']}/100")
        for blocker in result["blockers"]:
            print(f"- {blocker}")
    return 1 if args.strict and not result["ok"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
