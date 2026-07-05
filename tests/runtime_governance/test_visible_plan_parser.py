from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from runtime_governance import parse_visible_plan  # noqa: E402


COMPLETE_PLAN = """# Implementation Plan

## Task 1: Add visible plan parser

Goal:
Parse the AI-visible Markdown plan contract into internal task objects for maintainer validation.

Files:
- Inspect: src/runtime_governance/__init__.py
- Modify: src/runtime_governance/visible_plan_parser.py
- Test: tests/runtime_governance/test_visible_plan_parser.py

Acceptance Criteria:
- Parser returns one task with the expected title and visible fields.
- Parser keeps the visible Markdown text as the source of truth.

Verify:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_parser

Expected:
- unittest reports OK.

Review:
- Check parse behavior and field aliases.

Stop Conditions:
- Stop if the plan requires visible JSON metadata or hook state.

Rollback:
- Remove the parser module, export, and focused tests.
"""


class VisiblePlanParserTests(unittest.TestCase):
    def test_parses_visible_task_contract_fields(self) -> None:
        graph = parse_visible_plan(COMPLETE_PLAN)

        self.assertEqual(graph.title, "Implementation Plan")
        self.assertEqual(len(graph.tasks), 1)

        task = graph.tasks[0]
        self.assertEqual(task.task_id, "Task 1")
        self.assertEqual(task.title, "Add visible plan parser")
        self.assertIn("AI-visible Markdown", task.goal)
        self.assertIn(
            "Parser returns one task with the expected title and visible fields.",
            task.acceptance_criteria,
        )
        self.assertIn("python3 -m unittest", task.verify)
        self.assertIn("unittest reports OK", task.expected_output)
        self.assertIn("visible JSON metadata", task.stop_conditions)

    def test_parses_alias_labels(self) -> None:
        graph = parse_visible_plan(
            """# Implementation Plan

## Task A: Validate aliases
Goal: Accept common visible labels.
Inspect:
- docs/VALIDATION.md
Modify:
- src/runtime_governance/visible_plan_parser.py
Criteria:
- Aliases are parsed.
Verification:
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_parser
Expected output:
- OK
Review scope:
- Parser aliases only.
Stop condition:
- Stop on ambiguous label mapping.
Revert note:
- Revert parser alias changes.
Depends on:
- Task 0
"""
        )

        task = graph.tasks[0]
        self.assertEqual(task.files_to_inspect, ("docs/VALIDATION.md",))
        self.assertEqual(task.files_to_change, ("src/runtime_governance/visible_plan_parser.py",))
        self.assertEqual(task.acceptance_criteria, ("Aliases are parsed.",))
        self.assertEqual(task.dependencies, ("Task 0",))

    def test_parses_chinese_label_aliases_and_file_roles(self) -> None:
        graph = parse_visible_plan(
            """# 实施计划

## Task 1: 中文标签
目标：解析中文字段。
文件：
- 检查：`docs/VALIDATION.md`
- 修改：`src/runtime_governance/visible_plan_parser.py`
验收标准：
- 中文字段被解析。
验证：
- Command: python3 -m unittest tests.runtime_governance.test_visible_plan_parser
预期结果：
- OK
审查：
- Parser alias scope only.
停止条件：
- Stop on ambiguous label mapping.
回滚：
- Revert parser alias changes.
残余风险：
- Limited to parser behavior.
"""
        )

        task = graph.tasks[0]
        self.assertEqual(task.goal, "解析中文字段。")
        self.assertEqual(task.files_to_inspect, ("docs/VALIDATION.md",))
        self.assertEqual(task.files_to_change, ("src/runtime_governance/visible_plan_parser.py",))
        self.assertEqual(task.acceptance_criteria, ("中文字段被解析。",))
        self.assertIn("python3 -m unittest", task.verify)
        self.assertEqual(task.expected_output, "- OK")
        self.assertIn("Parser alias scope", task.review_scope)
        self.assertIn("ambiguous label", task.stop_conditions)
        self.assertIn("Revert parser alias changes", task.rollback_note)
        self.assertIn("Limited to parser behavior", task.residual_risk)

    def test_canonicalizes_prefixed_files_section_paths(self) -> None:
        graph = parse_visible_plan(
            """# Implementation Plan

## Task 1: Normalize plan files
Goal: Parse file roles from the visible Files section.
Files:
- Inspect: `src/a.py`
- Modify: `src/b.py` - parser implementation
- Test: `tests/test_b.py`
Verify:
- Command: python3 -m unittest tests.test_b
"""
        )

        task = graph.tasks[0]
        self.assertEqual(task.files_to_inspect, ("src/a.py", "tests/test_b.py"))
        self.assertEqual(task.files_to_change, ("src/b.py",))
        self.assertEqual(task.declared_files, ("src/a.py", "tests/test_b.py", "src/b.py"))


if __name__ == "__main__":
    unittest.main()
