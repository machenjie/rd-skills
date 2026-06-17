from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "generate-professional-scorecard.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("generate_professional_scorecard", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class GenerateProfessionalScorecardTests(unittest.TestCase):
    def test_missing_manifest_is_unknown_not_pass(self) -> None:
        module = _load_module()
        status, detail = module.profile_manifest_status(None, "recommended")
        self.assertEqual(status, "unknown")
        self.assertIn("not found", detail)

    def test_profile_manifest_count_mismatch_fails(self) -> None:
        module = _load_module()
        status, detail = module.profile_manifest_status(
            {
                "profile": "recommended",
                "top_level_skills": [],
                "professional_skills": [],
                "foundation_capabilities": [],
                "compiled_foundation_capabilities": [],
                "domain_extensions": [],
            },
            "recommended",
        )
        self.assertEqual(status, "fail")
        self.assertIn("top_level", detail)

    def test_foundation_needs_review_is_partial(self) -> None:
        module = _load_module()
        status = module._summary_status(
            "Foundation capability coverage",
            {"count": 40, "statuses": {"acceptable": 39, "needs-review": 1}},
        )
        self.assertEqual(status, "partial")

    def test_cli_writes_markdown_and_json(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            md_path = Path(tmp) / "scorecard.md"
            json_path = Path(tmp) / "scorecard.json"
            result = module.main(["--out", str(md_path), "--json-out", str(json_path)])
            self.assertEqual(result, 0)
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("dimensions", payload)
            self.assertIn("not_collected", payload["status_summary"])
            self.assertIn("# Professional Scorecard", md_path.read_text(encoding="utf-8"))

    def test_strict_profile_builds_rejects_unknown_manifest_dimension(self) -> None:
        module = _load_module()
        payload = {
            "dimensions": [
                {"name": "Registry source counts", "status": "pass"},
                {"name": "Profile build reproducibility", "status": "unknown"},
                {"name": "Example coverage", "status": "pass"},
                {"name": "Productization assets", "status": "pass"},
                {"name": "Hook safety", "status": "not_collected"},
                {"name": "Installation validation", "status": "not_collected"},
            ]
        }
        errors = module.strict_profile_build_errors(payload)
        self.assertTrue(any("Profile build reproducibility" in error for error in errors))

    def test_strict_profile_builds_allows_not_collected_release_dimensions(self) -> None:
        module = _load_module()
        payload = {
            "dimensions": [
                {"name": "Registry source counts", "status": "pass"},
                {"name": "Profile build reproducibility", "status": "pass"},
                {"name": "Example coverage", "status": "pass"},
                {"name": "Productization assets", "status": "pass"},
                {"name": "Hook safety", "status": "not_collected"},
                {"name": "Installation validation", "status": "not_collected"},
            ]
        }
        self.assertEqual(module.strict_profile_build_errors(payload), [])

    def test_open_source_readiness_no_license_is_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pyproject.toml").write_text('license = { text = "Proprietary" }\n', encoding="utf-8")
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "partial")
        self.assertIn("license_file=False", detail)

    def test_open_source_readiness_license_only_with_proprietary_metadata_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "Proprietary" }\n', encoding="utf-8")
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "fail")
        self.assertIn("pyproject_license_not_proprietary=False", detail)

    def test_open_source_readiness_license_and_metadata_without_security_is_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "MIT" }\n', encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text(
                "## Contribution Licensing\nContributions are accepted under the repository license.\n",
                encoding="utf-8",
            )
            (root / "SECURITY.md").write_text(
                "Use GitHub private vulnerability reporting when it is enabled.\n",
                encoding="utf-8",
            )
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "partial")
        self.assertIn("security_contact_confirmed=False", detail)

    def test_open_source_readiness_license_pyproject_and_security_pass(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "LICENSE").write_text("MIT\n", encoding="utf-8")
            (root / "pyproject.toml").write_text('license = { text = "MIT" }\n', encoding="utf-8")
            (root / "CONTRIBUTING.md").write_text(
                "## Contribution Licensing\nContributions are accepted under the repository license.\n",
                encoding="utf-8",
            )
            (root / "SECURITY.md").write_text(
                "GitHub private vulnerability reporting is enabled for this repository.\n",
                encoding="utf-8",
            )
            status, detail = module.open_source_readiness_status(root)
        self.assertEqual(status, "pass")
        self.assertIn("security_contact_confirmed=True", detail)


if __name__ == "__main__":
    unittest.main()
