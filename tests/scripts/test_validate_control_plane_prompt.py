from __future__ import annotations

import copy
import hashlib
import importlib.util
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_validator():
    spec = importlib.util.spec_from_file_location(
        "validate_control_plane_prompt_test_target",
        SCRIPTS / "validate-control-plane-prompt.py",
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load validate-control-plane-prompt.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


class ControlPromptTests(unittest.TestCase):
    def test_current_prompt_passes_exact_context_budget(self):
        text = VALIDATOR.PROMPT.read_text()
        self.assertEqual([], VALIDATOR.validate_prompt(text))
        self.assertLessEqual(VALIDATOR.count_o200k_base_tokens(text), 1750)

    def test_context_overflow_is_rejected(self):
        text = VALIDATOR.PROMPT.read_text() + (' Excess duplicated context.' * 2000)
        self.assertTrue(any('budget' in error for error in VALIDATOR.validate_prompt(text)))

    def test_retired_protocol_cannot_return_in_prompt(self):
        text = VALIDATOR.PROMPT.read_text() + '\nReview Round ID is required for completion.\n'
        self.assertTrue(any('retired machinery' in error for error in VALIDATOR.validate_prompt(text)))

    def test_worker_knowledge_delivery_cannot_be_removed_from_main(self):
        text = VALIDATOR.PROMPT.read_text()
        delivery = (
            "In each analysis-agent, task-agent, or review-agent assignment, direct it "
            "to apply the assigned Primary Professional Skill and selected Layer 3"
        )
        self.assertIn(delivery, text)
        for role in ("analysis-agent", "task-agent", "review-agent"):
            with self.subTest(role=role):
                names_only = text.replace(delivery, delivery.replace(role, "generic agent"))
                self.assertTrue(any(delivery in error for error in VALIDATOR.validate_prompt(names_only)))

    def test_worker_assignment_cannot_omit_resolved_primary_locator(self):
        text = VALIDATOR.PROMPT.read_text()
        locator = "Each assignment carries directly readable Host-resolved paths for Primary SKILL.md, selected Layer 3 bodies, and necessary Professional/Layer 3 Reference bodies"
        self.assertIn(locator, text)
        self.assertTrue(any(
            "Host-resolved paths" in error
            for error in VALIDATOR.validate_prompt(text.replace(locator, "name the Primary Professional Skill"))
        ))

    def test_analysis_and_review_branches_cannot_fall_back_to_names_only(self):
        text = VALIDATOR.PROMPT.read_text()
        for dispatch in (
            "A source-backed question or explicit diagnosis goes to analysis-agent with its Host-resolved Primary Professional Skill locator",
            "Send a concrete unresolved question to analysis-agent with that assignment's Host-resolved Primary Professional Skill locator",
            "provide the reviewer with its independently selected Review Primary Professional Skill locator and Layer 3",
        ):
            with self.subTest(dispatch=dispatch):
                self.assertTrue(any(
                    dispatch in error
                    for error in VALIDATOR.validate_prompt(text.replace(dispatch, dispatch.replace("locator", "name")))
                ))

    def test_assignment_content_reuse_host_loading_and_return_are_required(self):
        text = VALIDATOR.PROMPT.read_text()
        for guidance in (
            "Reuse supplied content; read missing bodies at those paths when relevant",
            "Return unavailable assets or selection-changing source evidence to Main before affected judgment",
            "Never guess roots or infer Worker asset visibility from Main discovery",
            "Project Skill names or calls do not replace the assigned Primary; reuse equivalent supplied content",
        ):
            with self.subTest(guidance=guidance):
                self.assertIn(guidance, text)
                self.assertTrue(any(
                    guidance in error
                    for error in VALIDATOR.validate_prompt(text.replace(guidance, ""))
                ))

    def test_reference_delivery_requires_direct_owner_loading_and_exact_state(self):
        text = VALIDATOR.PROMPT.read_text()
        for guidance in (
            "For unresolved References, carry owner partition Host paths and assign conditional reading",
            "Only exact References, including [], skip Reference selection",
            "read current Primary/selected Layer 3 owner partitions directly at their Host paths",
            "match required_by/load_when/do_not_load_when/required_output and context_admissibility",
            "Read needed record.path verbatim under that Professional Host root after safe relative-path validation",
        ):
            with self.subTest(guidance=guidance):
                self.assertIn(guidance, text)
                self.assertTrue(any(guidance in error for error in VALIDATOR.validate_prompt(text.replace(guidance, ""))))


if __name__ == '__main__':
    unittest.main()
