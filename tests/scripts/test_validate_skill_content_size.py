from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-skill-content-size.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_skill_content_size", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateSkillContentSizeExitPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = _load_module()

    def _run(self, findings: list[tuple[str, str, str]], *args: str) -> tuple[int, str]:
        stdout = io.StringIO()
        with (
            mock.patch.object(self.module, "check", return_value=(findings, [])),
            mock.patch.object(sys, "argv", [str(SCRIPT), *args]),
            contextlib.redirect_stdout(stdout),
        ):
            result = self.module.main()
        return result, stdout.getvalue()

    def test_professional_review_and_hard_gates_are_80_and_120_lines(self) -> None:
        self.assertEqual(self.module.THRESHOLDS["professional_review_lines"], 80)
        self.assertEqual(self.module.BODY_GATES["professional-skill"], 120)

    def test_body_line_hard_gate_cannot_be_excepted(self) -> None:
        self.assertNotIn("body_lines", self.module.VALID_ALLOW)
        self.assertNotIn("description_chars", self.module.VALID_ALLOW)
        self.assertNotIn("foundation_words", self.module.VALID_ALLOW)
        self.assertNotIn("foundation_tokens", self.module.VALID_ALLOW)
        self.assertNotIn("foundation_complex_words", self.module.VALID_ALLOW)
        for check_name in (
            "professional_words",
            "professional_tokens",
            "domain_words",
            "domain_tokens",
        ):
            self.assertNotIn(check_name, self.module.VALID_ALLOW)
            self.assertIn(check_name, self.module.HARD_FINDING_TYPES)
        self.assertEqual(
            self.module.audit.FOUNDATION_CONTENT_BUDGETS,
            {
                "compact": {"target_words": 400, "hard_words": 500},
                "complex": {"target_words": 500, "hard_words": 600},
            },
        )
        self.assertEqual(self.module.THRESHOLDS["foundation_hard_tokens"], 900)

    def test_description_hard_gates_are_centralized(self) -> None:
        self.assertIs(self.module.DESCRIPTION_BUDGETS, self.module.audit.DESCRIPTION_BUDGETS)
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["control-skill"]["hard"], 300
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["professional-skill"]["hard"], 300
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["foundation-capability"]["hard"], 260
        )
        self.assertEqual(
            self.module.DESCRIPTION_BUDGETS["domain-extension"]["hard"], 260
        )
        self.assertIsNone(
            self.module._description_hard_finding("professional-skill", "x" * 300)
        )
        self.assertIn(
            "301 chars",
            self.module._description_hard_finding(
                "professional-skill", "x" * 301
            ),
        )

    def test_control_root_is_included_in_hard_gate_scan(self) -> None:
        files = self.module._collect_files()
        self.assertIn(
            (
                "control-skill",
                ROOT / "src/control-skills/engineering-control-plane/SKILL.md",
            ),
            files,
        )

    def test_noncanonical_reference_projection_remains_in_size_scope(self) -> None:
        canonical = (
            "# Root\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "cache invalidation changes need failure coverage | "
            "no cache behavior or ownership changes | task-agent | checklist-result |\n"
        )
        self.assertNotIn(
            "cache invalidation",
            self.module.strip_registry_targeted_reference_projection(canonical),
        )
        for path in (
            "references/../checklist.md",
            "references//checklist.md",
            "references/./checklist.md",
        ):
            with self.subTest(path=path):
                noncanonical = canonical.replace(
                    "references/checklist.md",
                    path,
                )
                self.assertEqual(
                    noncanonical,
                    self.module.strip_registry_targeted_reference_projection(
                        noncanonical
                    ),
                )

    def test_size_budget_excludes_projection_only_with_proven_source_eof(self) -> None:
        body = (
            "# Fixture\n\n## Targeted References\n\n"
            "| Path | Type | Load when | Do not load when | Required by | Required output |\n"
            "|---|---|---|---|---|---|\n"
            "| [checklist](references/checklist.md) | decision-checklist | "
            "cache invalidation changes need failure coverage | "
            "no cache behavior or ownership changes | task-agent | checklist-result |"
        )
        prefix = "---\nname: fixture\ndescription: Fixture.\n---\n"
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "SKILL.md"
            with (
                mock.patch.object(self.module, "ROOT", Path(raw)),
                mock.patch.object(
                    self.module,
                    "_collect_files",
                    return_value=[("professional-skill", path)],
                ),
                mock.patch.object(self.module, "load_exceptions", return_value={}),
                mock.patch.object(
                    self.module.audit,
                    "_load_foundation_content_contracts",
                    return_value={},
                ),
                mock.patch.object(
                    self.module.audit,
                    "count_o200k_base_tokens",
                    side_effect=lambda text: (
                        1001 if "cache invalidation" in text else 1
                    ),
                ),
            ):
                path.write_text(prefix + body + "\n", encoding="utf-8")
                canonical_findings, canonical_errors = self.module.check()
                self.assertEqual([], canonical_errors)
                self.assertNotIn(
                    "professional_tokens",
                    {item[1] for item in canonical_findings},
                )

                path.write_text(prefix + body, encoding="utf-8")
                missing_eof_findings, missing_eof_errors = self.module.check()
                self.assertEqual([], missing_eof_errors)
                self.assertIn(
                    "professional_tokens",
                    {item[1] for item in missing_eof_findings},
                )

                crlf_source = (prefix + body + "\n").replace("\n", "\r\n")
                path.write_bytes(crlf_source.encode("utf-8"))
                crlf_findings, crlf_errors = self.module.check()
                self.assertEqual([], crlf_errors)
                self.assertIn(
                    "professional_tokens",
                    {item[1] for item in crlf_findings},
                )

    def test_default_fails_body_line_hard_gate_and_keeps_advisory_warning(self) -> None:
        result, output = self._run(
            [
                ("skill/SKILL.md", "body_lines", "body exceeds hard gate"),
                ("skill/SKILL.md", "section_lines", "section exceeds advisory gate"),
            ]
        )

        self.assertEqual(result, 1)
        self.assertIn("ERROR: skill/SKILL.md: [body_lines]", output)
        self.assertIn("WARN: skill/SKILL.md: [section_lines]", output)

    def test_default_fails_description_hard_gate(self) -> None:
        result, output = self._run(
            [("skill/SKILL.md", "description_chars", "description exceeds hard gate")]
        )

        self.assertEqual(result, 1)
        self.assertIn("ERROR: skill/SKILL.md: [description_chars]", output)

    def test_default_fails_foundation_word_hard_gate(self) -> None:
        result, output = self._run(
            [("skill/SKILL.md", "foundation_words", "body exceeds class hard limit")]
        )

        self.assertEqual(result, 1)
        self.assertIn("ERROR: skill/SKILL.md: [foundation_words]", output)

    def test_default_fails_foundation_token_hard_gate(self) -> None:
        result, output = self._run(
            [("skill/SKILL.md", "foundation_tokens", "body exceeds 900 tokens")]
        )

        self.assertEqual(result, 1)
        self.assertIn("ERROR: skill/SKILL.md: [foundation_tokens]", output)

    def test_default_fails_professional_and_domain_hard_gates(self) -> None:
        for check_name in (
            "professional_words",
            "professional_tokens",
            "domain_words",
            "domain_tokens",
        ):
            with self.subTest(check_name=check_name):
                result, output = self._run(
                    [("skill/SKILL.md", check_name, "governed body exceeds hard gate")]
                )
                self.assertEqual(1, result)
                self.assertIn(f"ERROR: skill/SKILL.md: [{check_name}]", output)

    def test_default_does_not_fail_advisory_finding(self) -> None:
        result, output = self._run(
            [("skill/SKILL.md", "repeated_phrase", "shared wording")]
        )

        self.assertEqual(result, 0)
        self.assertIn("WARN: skill/SKILL.md: [repeated_phrase]", output)

    def test_strict_promotes_advisory_finding_to_error(self) -> None:
        result, output = self._run(
            [("skill/SKILL.md", "table_rows", "table exceeds advisory gate")],
            "--strict",
        )

        self.assertEqual(result, 1)
        self.assertIn("ERROR: skill/SKILL.md: [table_rows]", output)


if __name__ == "__main__":
    unittest.main()
