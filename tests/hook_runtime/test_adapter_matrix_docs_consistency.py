from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "src" / "hook-runtime" / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from changeforge_adapter_capabilities import (  # noqa: E402
    docs_capability_matrix_from_text,
    format_docs_capability_matrix,
)


class AdapterMatrixDocsConsistencyTests(unittest.TestCase):
    def test_hooks_docs_matrix_matches_code_matrix(self) -> None:
        hooks_doc = (ROOT / "docs" / "HOOKS.md").read_text(encoding="utf-8")

        self.assertEqual(
            docs_capability_matrix_from_text(hooks_doc),
            format_docs_capability_matrix(),
        )


if __name__ == "__main__":
    unittest.main()
