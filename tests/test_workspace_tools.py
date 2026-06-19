from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from helpers import SCRIPT_DIR, create_workspace, make_valid_workspace

import sys

sys.path.insert(0, str(SCRIPT_DIR))

from assemble_prd import assemble  # noqa: E402
from add_source import add_source  # noqa: E402
from common import load_json, write_json_atomic  # noqa: E402
from confirm_item import confirm  # noqa: E402
from init_workspace import initialize  # noqa: E402
from status_workspace import status  # noqa: E402
from validate_prd import promote, validate  # noqa: E402


class WorkspaceToolTests(unittest.TestCase):
    def test_init_is_idempotent_and_resumes_from_nested_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workspace = create_workspace(root, "Resume Test")
            resumed, created = initialize("Resume Test", root, "enterprise", "b2b")
            self.assertFalse(created)
            self.assertEqual(workspace, resumed)

            nested = workspace / "notes" / "drafts"
            nested.mkdir(parents=True)
            from_nested, created_nested = initialize("Different Name", nested, "brief", "b2c")
            self.assertFalse(created_nested)
            self.assertEqual(workspace, from_nested)

    def test_assembly_requires_confirmed_module_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Marker Test")
            module = workspace / "prd" / "modules" / "01-module.md"
            module.write_text("# Draft module\n", encoding="utf-8")
            metadata = load_json(workspace / "workspace.json")
            metadata["confirmed_modules"] = ["01-module"]
            write_json_atomic(workspace / "workspace.json", metadata)
            with self.assertRaisesRegex(ValueError, "lacks confirmed status marker"):
                assemble(workspace)

    def test_manual_prd_edit_blocks_reassembly(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Conflict Test")
            prd = workspace / "prd" / "PRD.md"
            prd.write_text(prd.read_text(encoding="utf-8") + "\nManual edit\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed outside controlled assembly"):
                assemble(workspace)

    def test_valid_prd_can_promote_in_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Promotion Test")
            result, _ = validate(workspace)
            self.assertTrue(result["ok"])
            self.assertEqual(100, result["score"])

            promote(workspace, result, "review-ready")
            result_review, _ = validate(workspace)
            self.assertTrue(result_review["ok"])
            promote(workspace, result_review, "approved")
            self.assertEqual("approved", load_json(workspace / "workspace.json")["status"])

    def test_invalid_status_transition_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = make_valid_workspace(Path(temp), "Bad Promotion")
            result, _ = validate(workspace)
            with self.assertRaisesRegex(ValueError, "Invalid status transition"):
                promote(workspace, result, "approved")

    def test_add_source_generates_sequential_ids_and_rejects_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Source Test")
            first = add_source(str(workspace), "document", "brief.md", "business context", "high")
            second = add_source(str(workspace), "image", "screen.png", "current UI", "medium")
            self.assertEqual("SRC-002", first["source_id"])
            self.assertEqual("SRC-003", second["source_id"])
            with self.assertRaisesRegex(ValueError, "must not be empty"):
                add_source(str(workspace), "", "x", "y", "medium")

    def test_confirm_item_allows_only_valid_stage_and_blocks_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Confirm Test")
            with self.assertRaisesRegex(ValueError, "Unknown stage"):
                confirm(str(workspace), "stage", "not-a-stage")
            with self.assertRaisesRegex(ValueError, "unresolved markers"):
                confirm(str(workspace), "stage", "00-intake")
            stage = workspace / "shaping" / "00-intake.md"
            stage.write_text(
                stage.read_text(encoding="utf-8").replace("[TO CONFIRM]", "Confirmed"),
                encoding="utf-8",
            )
            result = confirm(str(workspace), "stage", "00-intake")
            self.assertTrue(result["ok"])

    def test_confirm_item_blocks_conflict_and_placeholder_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Blocker Test")
            stage = workspace / "shaping" / "00-intake.md"
            base = stage.read_text(encoding="utf-8").replace("[TO CONFIRM]", "ok")
            stage.write_text(base + "\n- [冲突] 两处来源矛盾\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unresolved markers"):
                confirm(str(workspace), "stage", "00-intake")
            stage.write_text(base + "\n- {{TODO}}\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "unresolved markers"):
                confirm(str(workspace), "stage", "00-intake")

    def test_confirm_item_requires_status_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Marker Required")
            stage = workspace / "shaping" / "00-intake.md"
            text = stage.read_text(encoding="utf-8").replace("[TO CONFIRM]", "ok")
            text = "\n".join(line for line in text.splitlines() if "stage-status" not in line)
            stage.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "status"):
                confirm(str(workspace), "stage", "00-intake")

    def test_confirm_plan_writes_depth_and_profile_and_blocks_auto(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Plan Test", "auto", "auto")
            plan = workspace / "prd" / "module-plan.md"
            plan.write_text(
                plan.read_text(encoding="utf-8").replace("[TO CONFIRM]", "复杂度适中"),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "auto"):
                confirm(str(workspace), "plan", None)
            result = confirm(str(workspace), "plan", None, "standard", "b2b")
            self.assertTrue(result["ok"])
            metadata = load_json(workspace / "workspace.json")
            self.assertEqual(metadata["depth"], "standard")
            self.assertEqual(metadata["product_profile"], "b2b")
            self.assertIn("plan-status: confirmed", plan.read_text(encoding="utf-8"))

    def test_confirm_review_without_blocking_decision_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Review Test")
            review = workspace / "review" / "action-items.md"
            review.write_text(
                review.read_text(encoding="utf-8").replace("[TO CONFIRM]", "无"),
                encoding="utf-8",
            )
            result = confirm(str(workspace), "review", "action-items")
            self.assertTrue(result["ok"])
            metadata = load_json(workspace / "workspace.json")
            self.assertEqual(metadata["review_status"]["action-items"], "confirmed")

    def test_status_workspace_reports_next_stage_and_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            workspace = create_workspace(Path(temp), "Status Test")
            result = status(str(workspace))
            self.assertEqual("00-discovery", result["next_stage"])
            self.assertFalse(result["validation"]["ok"])


if __name__ == "__main__":
    unittest.main()
