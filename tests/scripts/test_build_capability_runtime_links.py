from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build  # noqa: E402


class BuildCapabilityRuntimeLinksTests(unittest.TestCase):
    def test_rewrites_capability_owned_markdown_and_code_links(self) -> None:
        content = (
            "Load [checklist](references/checklist.md), "
            "[example](./examples/example-output.md), "
            "`references/evidence-patterns.md`, and "
            "`./examples/example-output.md`."
        )

        rewritten = build._rewrite_capability_runtime_links(
            content,
            "42-idempotency-retry-design",
        )

        self.assertIn(
            "[checklist](42-idempotency-retry-design/references/checklist.md)",
            rewritten,
        )
        self.assertIn(
            "[example](42-idempotency-retry-design/examples/example-output.md)",
            rewritten,
        )
        self.assertIn(
            "`42-idempotency-retry-design/references/evidence-patterns.md`",
            rewritten,
        )
        self.assertIn(
            "`42-idempotency-retry-design/examples/example-output.md`",
            rewritten,
        )

    def test_copies_capability_owned_references_and_examples(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            source = root / "src" / "foundation" / "capabilities" / "demo-capability"
            (source / "references").mkdir(parents=True)
            (source / "examples").mkdir()
            (source / "references" / "checklist.md").write_text(
                "# Checklist\n",
                encoding="utf-8",
            )
            (source / "examples" / "example-output.md").write_text(
                "# Example\n",
                encoding="utf-8",
            )
            capability = build.Capability(
                name="demo-capability",
                path=source,
                kind="foundation-capability",
                description="Use this capability when testing runtime asset copying.",
                version="0.1.0",
                metadata={},
                body="",
                capability_id="42",
                group="test",
                used_by=("owner-skill",),
                triggers=("test trigger",),
                risk_notes=("test risk",),
                expected_outputs=("test output",),
            )
            destination = root / "dist" / "references" / "capabilities" / "42-demo-capability"

            build._copy_capability_owned_runtime_assets(capability, destination)

            self.assertTrue((destination / "references" / "checklist.md").is_file())
            self.assertTrue((destination / "examples" / "example-output.md").is_file())


if __name__ == "__main__":
    unittest.main()
