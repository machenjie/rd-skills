from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-registry.py"


def _load_module() -> ModuleType:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_registry", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _configure_module(module, root: Path) -> None:
    registry_dir = root / "src" / "registry"
    module.ROOT = root
    module.REGISTRY_DIR = registry_dir
    module.STAGE_MODEL_REGISTRY = registry_dir / "stage-model.yaml"


def _write_registries(
    root: Path,
    routing_rules: str,
    stage_model: str,
) -> tuple[ModuleType, dict[str, object]]:
    registry_dir = root / "src" / "registry"
    registry_dir.mkdir(parents=True)
    routing_path = registry_dir / "routing-rules.yaml"
    routing_path.write_text(routing_rules, encoding="utf-8")
    (registry_dir / "stage-model.yaml").write_text(stage_model, encoding="utf-8")
    module = _load_module()
    _configure_module(module, root)
    return module, {"routing-rules.yaml": module.load_yaml_file(routing_path)}


class ValidateRegistryQualityGateTests(unittest.TestCase):
    """Regression coverage for canonical quality gate registry references."""

    def test_quality_gate_references_pass_when_declared(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            module, registry_data = _write_registries(
                Path(tmp_s),
                """
quality_gates:
  - security gate
risk_trigger_rules:
  - trigger: auth
    required_quality_gates: [security gate]
""",
                """
stages:
  - name: coding
    required_quality_gates:
      - security gate
""",
            )
            errors: list[str] = []
            module._validate_quality_gate_references(registry_data, errors)
        self.assertEqual(errors, [])

    def test_quality_gate_references_reject_unknown_risk_and_stage_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_s:
            module, registry_data = _write_registries(
                Path(tmp_s),
                """
quality_gates:
  - security gate
risk_trigger_rules:
  - trigger: auth
    required_quality_gates: [missing risk gate]
""",
                """
stages:
  - name: coding
    required_quality_gates:
      - missing stage gate
""",
            )
            errors: list[str] = []
            module._validate_quality_gate_references(registry_data, errors)
        joined = "\n".join(errors)
        self.assertIn("missing risk gate", joined)
        self.assertIn("missing stage gate", joined)


if __name__ == "__main__":
    unittest.main()
