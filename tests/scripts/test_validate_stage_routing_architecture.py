from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


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
    module.RUNTIME_ROUTE_RESOLVER = (
        root / "src" / "hook-runtime" / "scripts" / "changeforge_runtime_route_resolver.py"
    )


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
    id: "101"
  - name: agent-execution-discipline
    id: "102"
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


class RuntimeResolverRegistryConsistencyTests(unittest.TestCase):
    def test_runtime_resolver_registry_projection_passes_when_exact(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            _configure_module(module, tmp)
            _write_base_registries(
                tmp,
                """
risk_escalation_triggers: []
risk_trigger_rules: []
quality_gates: []
""",
            )
            errors: list[str] = []
            module._check_runtime_resolver_registry_consistency(
                _minimal_stage_model(),
                _minimal_resolver(),
                {"backend-change-builder", "security-privacy-gate"},
                {"ai-product-extension"},
                errors,
            )
        self.assertEqual(errors, [])

    def test_runtime_resolver_registry_projection_rejects_capability_id_drift(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp_s:
            tmp = Path(tmp_s)
            _configure_module(module, tmp)
            _write_base_registries(
                tmp,
                """
risk_escalation_triggers: []
risk_trigger_rules: []
quality_gates: []
""",
            )
            resolver = _minimal_resolver()
            resolver.CAPABILITY_IDS = {
                "implementation-structure-design": "999",
                "agent-execution-discipline": "102",
            }
            errors: list[str] = []
            module._check_runtime_resolver_registry_consistency(
                _minimal_stage_model(),
                resolver,
                {"backend-change-builder", "security-privacy-gate"},
                {"ai-product-extension"},
                errors,
            )
        self.assertTrue(any("CAPABILITY_IDS must match" in error for error in errors), errors)


def _minimal_stage_model() -> dict[str, object]:
    return {
        "stages": [
            {
                "name": "coding",
                "default_capabilities": ["implementation-structure-design"],
                "conditional_capabilities": ["agent-execution-discipline"],
            }
        ],
        "product_surfaces": [
            {
                "surface": "backend-product",
                "signals": ["backend", "service"],
                "required_skill": "backend-change-builder",
                "default_capabilities": ["implementation-structure-design"],
            }
        ],
        "language_surfaces": [
            {
                "language": "python",
                "capability": "agent-execution-discipline",
                "file_extensions": [".py"],
                "signals": ["python", "py"],
            }
        ],
    }


def _minimal_resolver() -> SimpleNamespace:
    return SimpleNamespace(
        PRODUCT_SURFACE_ORDER=("backend-product",),
        PRODUCT_SURFACE_SIGNALS={"backend-product": ("backend", "service")},
        LANGUAGE_FILE_EXTENSIONS={"python": (".py",)},
        LANGUAGE_CAPABILITIES={"python": "agent-execution-discipline"},
        LANGUAGE_SURFACE_SIGNALS={"python": ("python", "py")},
        PRODUCT_OWNER={"backend-product": "backend-change-builder"},
        DOMAIN_EXTENSION_BY_SURFACE={},
        SURFACE_CAPABILITIES={
            "backend-product": ("implementation-structure-design",),
        },
        STAGE_CAPABILITIES={"coding": ("implementation-structure-design",)},
        STAGE_CONDITIONAL_CAPABILITIES={"coding": ("agent-execution-discipline",)},
        CAPABILITY_IDS={
            "implementation-structure-design": "101",
            "agent-execution-discipline": "102",
        },
        ALL_DOMAIN_EXTENSIONS=("ai-product-extension",),
        DOMAIN_OWNER={"ai-product-extension": "security-privacy-gate"},
    )


if __name__ == "__main__":
    unittest.main()
