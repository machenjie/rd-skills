from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from repository_intelligence.graph.python_symbol_extractor import extract_python_source


class PythonSymbolExtractorTests(unittest.TestCase):
    def test_extracts_classes_functions_methods_and_imports(self) -> None:
        source = """
import os
from package.module import helper

class Worker:
    def run(self):
        return helper()

async def fetch():
    return os.getcwd()
"""
        extracted = extract_python_source(source)
        symbols = {(symbol["name"], symbol["kind"]) for symbol in extracted["symbols"]}
        self.assertIn(("Worker", "class"), symbols)
        self.assertIn(("Worker.run", "method"), symbols)
        self.assertIn(("fetch", "function"), symbols)
        self.assertTrue(all(symbol["line_start"] <= symbol["line_end"] for symbol in extracted["symbols"]))
        imports = extracted["imports"]
        self.assertIn("os", {item["module"] for item in imports})
        self.assertIn("package.module", {item["module"] for item in imports})

    def test_reports_parse_error_without_executing_code(self) -> None:
        extracted = extract_python_source("def broken(:\n")
        self.assertEqual(extracted["symbols"], [])
        self.assertEqual(extracted["references"][0]["kind"], "parse_error")


if __name__ == "__main__":
    unittest.main()
