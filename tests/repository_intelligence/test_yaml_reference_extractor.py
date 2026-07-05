from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.yaml_reference_extractor import extract_structured_file


class YamlReferenceExtractorTests(unittest.TestCase):
    def test_extracts_registry_entries_paths_and_capability_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capabilities.yaml"
            path.write_text(
                """---
schema_version: 1
kind: changeforge.capabilities
capabilities:
  - id: "01"
    name: repository-context-map
    path: src/foundation/capabilities/repository-context-map
    used_by: [change-impact-analyzer]
    required_capabilities: [context-packaging]
""",
                encoding="utf-8",
            )
            extracted = extract_structured_file(path, ROOT)
        self.assertEqual(extracted["frontmatter"]["kind"], "changeforge.capabilities")
        self.assertEqual(extracted["symbols"][0]["name"], "repository-context-map")
        values = {reference["value"] for reference in extracted["references"]}
        self.assertIn("src/foundation/capabilities/repository-context-map", values)
        self.assertIn("context-packaging", values)


if __name__ == "__main__":
    unittest.main()
