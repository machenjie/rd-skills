from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-open-source-readiness.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_open_source_readiness", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_base(root: Path, *, config: str | None = None, license_text: str = "Proprietary") -> None:
    (root / "config").mkdir(parents=True)
    (root / "pyproject.toml").write_text(
        "[project]\n"
        "name = \"sample\"\n"
        f"license = {{ text = \"{license_text}\" }}\n",
        encoding="utf-8",
    )
    (root / "CONTRIBUTING.md").write_text(
        "## Contribution Licensing\n"
        "Contributions are accepted under the repository license.\n",
        encoding="utf-8",
    )
    (root / "SECURITY.md").write_text(
        "GitHub private vulnerability reporting is enabled for this repository.\n",
        encoding="utf-8",
    )
    (root / "config" / "open-source-release.yaml").write_text(
        config
        or "schema_version: 1\n"
        "kind: changeforge.open_source_release\n"
        "selected_license: null\n"
        "contribution_licensing_confirmed: false\n"
        "security_contact_confirmed: false\n"
        "dist_release_policy: release-artifact-only\n",
        encoding="utf-8",
    )


class ValidateOpenSourceReadinessTests(unittest.TestCase):
    def test_repository_default_is_partial_not_fail(self) -> None:
        module = _load_module()
        result = module.evaluate_open_source_readiness(ROOT)
        self.assertEqual(result.status, "partial")
        self.assertFalse(result.checks["license_file"])
        self.assertIn("owner license decision", "\n".join(result.warnings))

    def test_missing_license_is_partial_when_owner_has_not_selected_license(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(root)
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "partial")
        self.assertFalse(result.checks["license_file"])

    def test_license_with_proprietary_pyproject_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(root)
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("pyproject.toml license metadata is proprietary" in error for error in result.errors))

    def test_selected_license_requires_license_file_and_non_proprietary_metadata(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(
                root,
                config=(
                    "schema_version: 1\n"
                    "kind: changeforge.open_source_release\n"
                    "selected_license: MIT\n"
                    "contribution_licensing_confirmed: true\n"
                    "security_contact_confirmed: true\n"
                    "dist_release_policy: release-artifact-only\n"
                ),
            )
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "fail")
        self.assertTrue(any("root LICENSE is missing" in error for error in result.errors))
        self.assertTrue(any("pyproject.toml license metadata is proprietary" in error for error in result.errors))

    def test_non_proprietary_without_confirmations_is_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(root, license_text="MIT")
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "partial")
        self.assertFalse(result.checks["selected_license_non_null"])
        self.assertFalse(result.checks["contribution_licensing_confirmed"])
        self.assertFalse(result.checks["security_contact_confirmed"])

    def test_all_owner_confirmations_pass(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(
                root,
                config=(
                    "schema_version: 1\n"
                    "kind: changeforge.open_source_release\n"
                    "selected_license: MIT\n"
                    "contribution_licensing_confirmed: true\n"
                    "security_contact_confirmed: true\n"
                    "dist_release_policy: release-artifact-only\n"
                ),
                license_text="MIT",
            )
            (root / "LICENSE").write_text("MIT License\n", encoding="utf-8")
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "pass")

    def test_invalid_license_or_dist_policy_fails(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(
                root,
                config=(
                    "schema_version: 1\n"
                    "kind: changeforge.open_source_release\n"
                    "selected_license: Made-Up-License\n"
                    "contribution_licensing_confirmed: false\n"
                    "security_contact_confirmed: false\n"
                    "dist_release_policy: publish-everywhere\n"
                ),
                license_text="MIT",
            )
            result = module.evaluate_open_source_readiness(root)
        self.assertEqual(result.status, "fail")
        joined = "\n".join(result.errors)
        self.assertIn("selected_license must be one of", joined)
        self.assertIn("dist_release_policy must be one of", joined)

    def test_main_require_pass_fails_for_partial(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_base(root)
            self.assertEqual(module.main(["--root", str(root)]), 0)
            self.assertEqual(module.main(["--root", str(root), "--require-pass"]), 1)


if __name__ == "__main__":
    unittest.main()
