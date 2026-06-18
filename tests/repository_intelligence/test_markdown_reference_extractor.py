from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.markdown_reference_extractor import extract_markdown_source


class MarkdownReferenceExtractorTests(unittest.TestCase):
    def test_extracts_frontmatter_headings_links_and_code_references(self) -> None:
        source = """---
name: repository-context-map
triggers: [repo graph, context pack]
---
# Repository Context
Use `context-packaging` and [registry](../../registry/capabilities.yaml).
See `src/hook-runtime/scripts/changeforge_runtime_adapters.py`.
"""
        extracted = extract_markdown_source(source, "src/foundation/capabilities/repository-context-map/SKILL.md")
        self.assertEqual(extracted["frontmatter"]["name"], "repository-context-map")
        self.assertEqual(extracted["headings"][0]["name"], "Repository Context")
        values = {reference["value"] for reference in extracted["references"]}
        self.assertIn("context-packaging", values)
        self.assertIn("../../registry/capabilities.yaml", values)
        self.assertIn("src/hook-runtime/scripts/changeforge_runtime_adapters.py", values)


if __name__ == "__main__":
    unittest.main()
