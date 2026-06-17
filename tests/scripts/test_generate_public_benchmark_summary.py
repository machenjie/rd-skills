from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-public-benchmark-summary.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_public_benchmark_summary", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GeneratePublicBenchmarkSummaryTests(unittest.TestCase):
    def test_missing_evidence_is_unknown_or_not_collected(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            payload = module.generate_summary(root)

        statuses = {item["name"]: item["status"] for item in payload["items"]}
        self.assertEqual(statuses["Release readiness"], "unknown")
        self.assertEqual(statuses["Installation validation"], "not_collected")
        self.assertEqual(statuses["Marketplace validation"], "not_collected")
        self.assertNotIn("pass", {statuses["Release readiness"], statuses["Installation validation"]})

    def test_markdown_states_claim_boundary(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            markdown = module.render_markdown(module.generate_summary(root))

        self.assertIn("local deterministic ChangeForge evidence", markdown)
        self.assertIn("does not claim external popularity", markdown)
        self.assertIn("## Known Unknowns / Not Collected", markdown)

    def test_check_mode_catches_stale_outputs(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            out = root / "summary.md"
            json_out = root / "summary.json"
            (root / "pyproject.toml").write_text(
                "[project]\nname = \"sample\"\nversion = \"0.1.0\"\n",
                encoding="utf-8",
            )
            out.write_text("stale\n", encoding="utf-8")
            json_out.write_text("{}\n", encoding="utf-8")
            old_root = module.ROOT
            module.ROOT = root
            try:
                self.assertEqual(
                    module.main(["--check", "--out", str(out), "--json-out", str(json_out)]),
                    1,
                )
                self.assertEqual(module.main(["--out", str(out), "--json-out", str(json_out)]), 0)
                self.assertEqual(
                    module.main(["--check", "--out", str(out), "--json-out", str(json_out)]),
                    0,
                )
            finally:
                module.ROOT = old_root


if __name__ == "__main__":
    unittest.main()
