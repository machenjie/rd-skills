from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-stage-routing-architecture.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_stage_routing", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_registry(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def _configure_module(module, root: Path) -> None:
    registry = root / "src" / "registry"
    module.ROOT = root
    module.REGISTRY_DIR = registry
    module.ROUTING_RULES_REGISTRY = registry / "routing-rules.yaml"
    module.SKILLS_REGISTRY = registry / "skills.yaml"
    module.CAPABILITIES_REGISTRY = registry / "capabilities.yaml"
    module.DOMAIN_EXTENSIONS_REGISTRY = registry / "domain-extensions.yaml"


def _write_base_registries(root: Path, routing_rules: str) -> None:
    registry = root / "src" / "registry"
    _write_registry(
        registry / "skills.yaml",
        """
skills:
  - name: security-privacy-gate
  - name: backend-change-builder
""",
    )
    _write_registry(
        registry / "capabilities.yaml",
        """
capabilities:
  - name: implementation-structure-design
  - name: agent-execution-discipline
""",
    )
    _write_registry(
        registry / "domain-extensions.yaml",
        """
domain_extensions:
  - name: ai-product-extension
""",
    )
    _write_registry(registry / "routing-rules.yaml", routing_rules)


class RiskTriggerRuleValidationTests(unittest.TestCase):
    def test_risk_trigger_rules_pass_when_triggers_and_references_match(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            _configure_module(module, tmp)
            _write_base_registries(
                tmp,
                """
risk_escalation_triggers:
  - auth
  - AI prompt
risk_trigger_rules:
  - trigger: auth
    required_skills: [security-privacy-gate]
    required_capabilities: [agent-execution-discipline]
    required_quality_gates: [security gate]
  - trigger: AI prompt
    required_domain_extensions: [ai-product-extension]
quality_gates:
  - security gate
""",
            )
            errors: list[str] = []
            module._check_risk_trigger_rules(errors)
        self.assertEqual(errors, [])

    def test_risk_trigger_rules_require_bidirectional_trigger_coverage(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            _configure_module(module, tmp)
            _write_base_registries(
                tmp,
                """
risk_escalation_triggers:
  - auth
  - webhook
risk_trigger_rules:
  - trigger: auth
    required_skills: [security-privacy-gate]
  - trigger: undeclared trigger
    required_skills: [security-privacy-gate]
quality_gates:
  - security gate
""",
            )
            errors: list[str] = []
            module._check_risk_trigger_rules(errors)
        joined = "\n".join(errors)
        self.assertIn("'webhook' has no matching risk_trigger_rules entry", joined)
        self.assertIn("'undeclared trigger' is not declared", joined)

    def test_risk_trigger_rules_reject_unknown_registry_references(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            _configure_module(module, tmp)
            _write_base_registries(
                tmp,
                """
risk_escalation_triggers:
  - auth
risk_trigger_rules:
  - trigger: auth
    required_skills: [missing-skill]
    required_capabilities: [missing-capability]
    required_domain_extensions: [missing-extension]
    required_quality_gates: [missing gate]
quality_gates:
  - security gate
""",
            )
            errors: list[str] = []
            module._check_risk_trigger_rules(errors)
        joined = "\n".join(errors)
        self.assertIn("unknown skill 'missing-skill'", joined)
        self.assertIn("unknown capability 'missing-capability'", joined)
        self.assertIn("unknown domain extension 'missing-extension'", joined)
        self.assertIn("unknown quality gate 'missing gate'", joined)


if __name__ == "__main__":
    unittest.main()
