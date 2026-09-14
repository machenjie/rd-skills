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
            "In each Worker assignment, direct it to apply the assigned Primary "
            "Professional Skill and selected Layer 3"
        )
        self.assertIn(delivery, text)
        self.assertTrue(any(
            "Worker assignment" in error
            for error in VALIDATOR.validate_prompt(text.replace(delivery, ""))
        ))

    def test_assignment_content_reuse_host_loading_and_return_are_required(self):
        text = VALIDATOR.PROMPT.read_text()
        for guidance in (
            "reuse supplied content or load missing content from the Host-selected "
            "Professional entrypoint and its Layer 3 Delivery when decision-relevant",
            "Return unavailable assets or selection-changing source evidence to Main",
        ):
            with self.subTest(guidance=guidance):
                self.assertIn(guidance, text)
                self.assertTrue(any(
                    guidance in error
                    for error in VALIDATOR.validate_prompt(text.replace(guidance, ""))
                ))


if __name__ == '__main__':
    unittest.main()
