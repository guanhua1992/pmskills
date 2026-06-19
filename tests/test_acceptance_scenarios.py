from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import (
    CN_VALID_MODULE,
    SCRIPT_DIR,
    add_duplicate_requirement,
    create_workspace,
    make_valid_workspace,
)

import sys

sys.path.insert(0, str(SCRIPT_DIR))

from validate_prd import validate  # noqa: E402


class AcceptanceScenarioTests(unittest.TestCase):
    def test_one_line_ambiguous_request_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Make onboarding better", "auto", "auto")
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertLess(result["score"], 85)
            self.assertTrue(result["blockers"])

    def test_standard_b2c_prd_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Consumer Checkout", "standard", "b2c")
            result, _ = validate(workspace)
            self.assertTrue(result["ok"])

    def test_enterprise_b2b_prd_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Approval Workflow", "enterprise", "b2b")
            result, _ = validate(workspace)
            self.assertTrue(result["ok"])

    def test_ai_data_prd_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Insight Assistant", "enterprise", "ai-data")
            result, _ = validate(workspace)
            self.assertTrue(result["ok"])

    def test_duplicate_requirement_id_blocks_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Duplicate ID")
            add_duplicate_requirement(workspace)
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Duplicates" in blocker for blocker in result["blockers"]))

    def test_missing_evidence_trace_blocks_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Missing Evidence")
            prd = workspace / "prd" / "PRD.md"
            text = prd.read_text(encoding="utf-8").replace("SRC-001", "SRC-999")
            prd.write_text(text, encoding="utf-8")
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Missing evidence" in blocker for blocker in result["blockers"]))

    def test_existing_need_without_value_judgment_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "No Value Judgment")
            stage = workspace / "shaping" / "01-value-and-truth.md"
            stage.write_text(
                stage.read_text(encoding="utf-8").replace("Confirmed", "[TO CONFIRM]", 1),
                encoding="utf-8",
            )
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("analysis" in blocker for blocker in result["blockers"]))

    def test_b2b_prd_missing_permission_matrix_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "B2B Missing Permission", "enterprise", "b2b")
            prd = workspace / "prd" / "PRD.md"
            prd.write_text(
                prd.read_text(encoding="utf-8").replace("Permission Matrix", "Access Table"),
                encoding="utf-8",
            )
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("b2b" in blocker for blocker in result["blockers"]))

    def test_ai_data_missing_evaluation_and_fallback_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "AI Missing Evaluation", "enterprise", "ai-data")
            prd = workspace / "prd" / "PRD.md"
            text = prd.read_text(encoding="utf-8")
            for term in ("Evaluation", "Dataset", "Human Review", "Fallback"):
                text = text.replace(term, "Removed")
            prd.write_text(text, encoding="utf-8")
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("ai-data" in blocker for blocker in result["blockers"]))

    def test_vibe_spec_missing_outputs_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Missing Vibe Output")
            prd = workspace / "prd" / "PRD.md"
            prd.write_text(
                prd.read_text(encoding="utf-8").replace(
                    "| Outputs | Completed result, persisted data, monitoring event. |",
                    "",
                ),
                encoding="utf-8",
            )
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Outputs" in blocker for blocker in result["blockers"]))

    def test_chinese_prd_with_fullwidth_colon_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(
                Path(temp), "中文 PRD", "standard", "general", module_text=CN_VALID_MODULE
            )
            result, _ = validate(workspace)
            self.assertTrue(result["ok"], result["blockers"])
            self.assertEqual(result["max_score"], 115)

    def test_auto_profile_blocks_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Auto Profile", "standard", "auto")
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("auto" in blocker for blocker in result["blockers"]))

    def test_general_missing_platform_coverage_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "General Missing Platform", "standard", "general")
            prd = workspace / "prd" / "PRD.md"
            text = prd.read_text(encoding="utf-8")
            for term in ("Compatibility", "operations", "Operations", "Platform", "平台", "Support"):
                text = text.replace(term, "Removed")
            prd.write_text(text, encoding="utf-8")
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("general" in blocker for blocker in result["blockers"]))

    def test_blocking_review_prevents_finalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Blocking Review")
            review = workspace / "review" / "technical-review.md"
            review.write_text(
                review.read_text(encoding="utf-8").replace(
                    "| Blocking decision | no |",
                    "| Blocking decision | yes |",
                ),
                encoding="utf-8",
            )
            result, _ = validate(workspace)
            self.assertFalse(result["ok"])
            self.assertTrue(any("Review blockers" in blocker for blocker in result["blockers"]))


if __name__ == "__main__":
    unittest.main()
