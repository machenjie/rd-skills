from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validate-runtime-reference-links.py"


def _run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(VALIDATOR),
            "--root",
            str(root),
            "--profile",
            "recommended",
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        check=False,
    )


class ValidateRuntimeReferenceLinksTests(unittest.TestCase):
    def test_existing_local_markdown_link_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "recommended" / "change-forge-router"
            refs = profile / "references"
            refs.mkdir(parents=True)
            (profile / "SKILL.md").write_text(
                "Read [rules](references/routing-rules.md).\n",
                encoding="utf-8",
            )
            (refs / "routing-rules.md").write_text("# Rules\n", encoding="utf-8")

            result = _run_validator(Path(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("validated local Markdown links", result.stdout)

    def test_missing_local_markdown_link_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "recommended" / "change-forge-router"
            profile.mkdir(parents=True)
            (profile / "SKILL.md").write_text(
                "Read [missing](references/missing.md).\n",
                encoding="utf-8",
            )

            result = _run_validator(Path(tmp))

        self.assertEqual(result.returncode, 1)
        self.assertIn("missing local runtime reference", result.stderr)

    def test_source_dev_only_reference_is_not_runtime_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "recommended" / "backend-change-builder"
            profile.mkdir(parents=True)
            (profile / "SKILL.md").write_text(
                "Source/dev-only deep reference: `references/not-copied.md`.\n",
                encoding="utf-8",
            )

            result = _run_validator(Path(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_skill_root_code_reference_from_nested_reference_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "recommended" / "ai-code-review-refactor"
            refs = profile / "references" / "capabilities"
            refs.mkdir(parents=True)
            (refs / "103-skill-authoring-expert.md").write_text(
                "Load `references/capabilities/index.md` when selected.\n",
                encoding="utf-8",
            )
            (refs / "index.md").write_text("# Capability Index\n", encoding="utf-8")

            result = _run_validator(Path(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_code_reference_examples_are_not_runtime_contracts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp) / "recommended" / "acceptance-criteria-builder"
            profile.mkdir(parents=True)
            (profile / "SKILL.md").write_text(
                "Examples:\n"
                "- `42 idempotency-retry-design` -> "
                "`references/capabilities/42-idempotency-retry-design.md`\n",
                encoding="utf-8",
            )

            result = _run_validator(Path(tmp))

        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
