from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-productization-assets.py"
VALIDATE_HOOKS = ROOT / "scripts" / "validate-hooks.py"
VALIDATE_INSTALLATION = ROOT / "scripts" / "validate-installation.py"


def _load_module():
    return _load_script(SCRIPT, "validate_productization_assets")


def _load_script(path: Path, name: str):
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateProductizationAssetsTests(unittest.TestCase):
    def test_repository_productization_assets_validate(self) -> None:
        module = _load_module()
        self.assertEqual(module.validate_productization_assets(ROOT), [])

    def test_validate_hooks_writes_machine_readable_reports(self) -> None:
        module = _load_script(VALIDATE_HOOKS, "validate_hooks_report_test")
        for name in (
            "_validate_required_files",
            "_validate_python_files",
            "_validate_adapter_capabilities",
            "_validate_schema_files",
            "_validate_bootstrap_fragment",
            "_validate_hook_behavior",
            "_validate_runtime_route_resolver",
        ):
            setattr(module, name, lambda errors: None)
        module._load_json = lambda path, errors: {}
        module._validate_template = lambda *args, **kwargs: None
        module._validate_copilot_template = lambda *args, **kwargs: None

        class DummyCapabilities:
            def format_coverage_matrix(self) -> str:
                return "adapter coverage matrix"

            def docs_capability_matrix_from_text(self, text: str) -> str:
                return "adapter docs matrix"

            def format_docs_capability_matrix(self) -> str:
                return "adapter docs matrix"

        module._load_adapter_capabilities = lambda errors: DummyCapabilities()

        with tempfile.TemporaryDirectory() as tmp:
            json_out = Path(tmp) / "hook-validation.json"
            md_out = Path(tmp) / "hook-validation.md"
            result = module.main(["--json-out", str(json_out), "--out", str(md_out)])
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            markdown = md_out.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["generated_by"], "scripts/validate-hooks.py")
        self.assertIn("# Hook Validation", markdown)

    def test_validate_installation_writes_machine_readable_reports(self) -> None:
        module = _load_script(VALIDATE_INSTALLATION, "validate_installation_report_test")
        module._load_registry_sets = lambda errors: {
            "professional_names": set(),
            "capability_names": set(),
            "domain_extension_names": set(),
            "capability_files_by_skill": {},
        }
        for name in (
            "_validate_dist_guardrails",
            "_validate_profile_roots",
            "_validate_hook_runtime",
            "_validate_zips",
        ):
            setattr(module, name, lambda *args, **kwargs: None)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            module.DIST_DIR = root / "dist"
            module.DIST_DIR.mkdir()
            module.REQUIRED_DIST_DIRS = ()
            module.PROFILE_SKILL_ROOTS = ()
            module.REQUIRED_HOOK_DIST_FILES = ()
            json_out = root / "installation-validation.json"
            md_out = root / "installation-validation.md"
            result = module.main(["--json-out", str(json_out), "--out", str(md_out)])
            payload = json.loads(json_out.read_text(encoding="utf-8"))
            markdown = md_out.read_text(encoding="utf-8")

        self.assertEqual(result, 0)
        self.assertEqual(payload["status"], "pass")
        self.assertEqual(payload["generated_by"], "scripts/validate-installation.py")
        self.assertIn("# Installation Validation", markdown)


if __name__ == "__main__":
    unittest.main()
