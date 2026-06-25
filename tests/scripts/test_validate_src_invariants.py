from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))


def _load_validator():
    path = SCRIPTS / "validate-src-invariants.py"
    spec = importlib.util.spec_from_file_location("validate_src_invariants_under_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


validator = _load_validator()


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _skills_registry(*names: str) -> str:
    entries = "\n".join(
        f"  - name: {name}\n    path: src/professional-skills/{name}" for name in names
    )
    return f"---\nschema_version: 1\nkind: changeforge.skills\nskills:\n{entries}\n"


def _domain_extensions_registry(*names: str) -> str:
    entries = "\n".join(
        f"  - name: {name}\n    path: src/domain-extensions/{name}" for name in names
    )
    return (
        "---\nschema_version: 1\nkind: changeforge.domain_extensions\n"
        f"domain_extensions:\n{entries}\n"
    )


def _professional_skill(name: str) -> str:
    required = "\n".join(f"# {section}\nContent.\n" for section in validator.PROFESSIONAL_REQUIRED_SECTIONS)
    return (
        "---\n"
        f"name: {name}\n"
        "changeforge_kind: professional-skill\n"
        "license: MIT\n"
        "changeforge_version: \"1.0\"\n"
        "---\n"
        f"{required}"
    )


def _capabilities_registry(*capabilities: str) -> str:
    return (
        "---\nschema_version: 1\nkind: changeforge.capabilities\n"
        "capabilities:\n"
        + "\n".join(capabilities)
    )


def _capability_entry(
    *,
    capability_id: str = "01",
    name: str = "test-capability",
    used_by: str = "[owner-skill]",
    route_level: bool = False,
) -> str:
    route_line = "    route_level_capability: true\n" if route_level else ""
    return (
        f"  - id: \"{capability_id}\"\n"
        f"    name: {name}\n"
        "    group: test\n"
        f"    path: src/foundation/capabilities/{name}\n"
        "    status: implemented\n"
        f"    used_by: {used_by}\n"
        "    triggers: [test trigger]\n"
        "    risk_notes: [test risk]\n"
        "    expected_outputs: [test output]\n"
        f"{route_line}"
    )


class ValidateSrcInvariantsTests(unittest.TestCase):
    def tearDown(self) -> None:
        validator._set_root(ROOT)

    def test_current_repository_passes(self) -> None:
        result = validator.validate_repository(ROOT)

        self.assertEqual([], result.errors)

    def test_missing_skill_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src/registry/skills.yaml", _skills_registry("missing-skill"))
            validator._set_root(root)

            errors: list[str] = []
            validator._validate_skill_registry(errors)

        self.assertTrue(any("missing path src/professional-skills/missing-skill" in error for error in errors))

    def test_skill_frontmatter_name_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src/registry/skills.yaml", _skills_registry("owner-skill"))
            _write(
                root / "src/professional-skills/owner-skill/SKILL.md",
                _professional_skill("different-name"),
            )
            validator._set_root(root)

            errors: list[str] = []
            validator._validate_skill_registry(errors)

        self.assertTrue(any("frontmatter name 'different-name' must match" in error for error in errors))

    def test_unknown_capability_used_by_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src/registry/skills.yaml", _skills_registry("owner-skill"))
            _write(root / "src/registry/domain-extensions.yaml", _domain_extensions_registry("domain-owner"))
            _write(
                root / "src/registry/capabilities.yaml",
                _capabilities_registry(_capability_entry(used_by="[missing-owner]")),
            )
            _write(root / "src/foundation/capabilities/test-capability/SKILL.md", "# Capability\n")
            validator._set_root(root)

            errors: list[str] = []
            warnings: list[str] = []
            validator._validate_capability_registry(errors, warnings)

        self.assertTrue(any("used_by references unknown item(s): missing-owner" in error for error in errors))

    def test_route_level_capability_classification_does_not_false_fail(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src/registry/skills.yaml", _skills_registry("change-forge-router"))
            _write(root / "src/registry/domain-extensions.yaml", _domain_extensions_registry())
            _write(
                root / "src/registry/capabilities.yaml",
                _capabilities_registry(
                    _capability_entry(
                        capability_id="120",
                        name="agent-execution-discipline",
                        used_by="[change-forge-router]",
                        route_level=True,
                    )
                ),
            )
            _write(root / "src/foundation/capabilities/agent-execution-discipline/SKILL.md", "# Capability\n")
            validator._set_root(root)

            errors: list[str] = []
            warnings: list[str] = []
            validator._validate_capability_registry(errors, warnings)

        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_domain_extension_capability_owner_is_valid(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(root / "src/registry/skills.yaml", _skills_registry("owner-skill"))
            _write(root / "src/registry/domain-extensions.yaml", _domain_extensions_registry("domain-owner"))
            _write(
                root / "src/registry/capabilities.yaml",
                _capabilities_registry(_capability_entry(used_by="[domain-owner]")),
            )
            _write(root / "src/foundation/capabilities/test-capability/SKILL.md", "# Capability\n")
            validator._set_root(root)

            errors: list[str] = []
            warnings: list[str] = []
            validator._validate_capability_registry(errors, warnings)

        self.assertEqual([], errors)
        self.assertTrue(any("no direct or indirect professional skill owner" in warning for warning in warnings))

    def test_generated_capability_reference_without_source_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            ref = (
                root
                / "dist/universal/skills/recommended/change-forge-router/references/capabilities/999-missing.md"
            )
            _write(ref, f"{validator.GENERATED_MARKER}\n# Missing\n")
            validator._set_root(root)

            errors: list[str] = []
            warnings: list[str] = []
            validator._validate_capability_references(
                [{"id": "01", "name": "known", "used_by": ["change-forge-router"]}],
                errors,
                warnings,
            )

        self.assertTrue(any("does not map to a registry capability" in error for error in errors))

    def test_source_dist_boundary_violation_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            _write(
                root / "dist/universal/skills/recommended/owner-skill/SKILL.md",
                "This runtime skill points at src/registry/skills.yaml.",
            )
            validator._set_root(root)

            errors: list[str] = []
            validator._validate_dist_guardrails(errors)

        self.assertTrue(any("runtime content must not reference src/registry" in error for error in errors))

    def test_domain_extension_missing_skill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "src/domain-extensions/web3-product-extension").mkdir(parents=True)
            _write(
                root / "src/professional-skills/change-forge-router/SKILL.md",
                "web3-product-extension is selected from a domain signal.",
            )
            validator._set_root(root)

            errors: list[str] = []
            validator._validate_domain_extensions(errors)

        self.assertTrue(any("must contain SKILL.md" in error for error in errors))

    def test_hook_docs_matrix_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            docs = root / "docs/HOOKS.md"
            rows = [
                ("Codex", "`SessionStart`", "No"),
                ("Claude", "none", "No"),
                ("Copilot", "none", "No"),
                ("Generic fallback", "none", "No"),
                ("Cline staged target", "none", "No"),
                ("Roo staged target", "none", "No"),
                ("OpenHands backend target", "none", "No"),
                ("Gemini CLI placeholder", "none", "No"),
                ("Goose placeholder", "none", "No"),
            ]
            table = [
                "| Runtime | Supported events | Unsupported events | Advisory context | Enforcement | Notes |",
                "| --- | --- | --- | --- | --- | --- |",
                *[f"| {label} | {supported} | none | {advisory} | warn | test |" for label, supported, advisory in rows],
            ]
            _write(docs, "\n".join(table))

            def adapter_capabilities_for(runtime: str):
                supported = ("SessionStart", "Stop") if runtime == "codex" else ()
                return types.SimpleNamespace(
                    supported_events=supported,
                    advisory_context_supported=False,
                )

            errors: list[str] = []
            warnings: list[str] = []
            validator._compare_docs_adapter_matrix(
                docs,
                types.SimpleNamespace(adapter_capabilities_for=adapter_capabilities_for),
                errors,
                warnings,
            )

        self.assertTrue(any("Codex supported events differ" in error for error in errors))

    def test_validation_broker_missing_runtime_governance_mapping_fails(self) -> None:
        original_import_required_module = validator._import_required_module
        fake_module = types.SimpleNamespace(
            REGISTRY={
                "registry": {
                    "path_patterns": (
                        "src/registry/**",
                        "src/professional-skills/**",
                        "src/foundation/capabilities/**",
                        "src/domain-extensions/**",
                        "src/hook-runtime/**",
                        "src/project_memory/**",
                        "src/repository_intelligence/**",
                        "src/validation_broker/**",
                        "src/trajectory/**",
                    )
                }
            }
        )
        validator._import_required_module = lambda *args, **kwargs: fake_module
        try:
            errors: list[str] = []
            validator._validate_validation_broker_mapping(errors)
        finally:
            validator._import_required_module = original_import_required_module

        self.assertTrue(any("src/runtime_governance/**" in error for error in errors))

    def test_hook_runtime_adapter_import_failure_is_error(self) -> None:
        errors = _hook_runtime_import_errors("src/runtime_governance/adapters/base.py")

        self.assertTrue(
            any("src/runtime_governance/adapters/base.py: import failed:" in error for error in errors),
            errors,
        )

    def test_runtime_events_import_failure_is_error(self) -> None:
        errors = _hook_runtime_import_errors("src/runtime_governance/events.py")

        self.assertTrue(
            any("src/runtime_governance/events.py: import failed:" in error for error in errors),
            errors,
        )

    def test_runtime_gates_import_failure_is_error(self) -> None:
        errors = _hook_runtime_import_errors("src/runtime_governance/gates.py")

        self.assertTrue(
            any("src/runtime_governance/gates.py: import failed:" in error for error in errors),
            errors,
        )

    def test_validation_broker_registry_import_failure_is_error(self) -> None:
        original_import_module_result = validator._import_module_result
        validator._import_module_result = lambda *args, **kwargs: validator.ImportResult(
            None,
            "ImportError: registry boom",
        )
        try:
            errors: list[str] = []
            validator._validate_validation_broker_mapping(errors)
        finally:
            validator._import_module_result = original_import_module_result

        self.assertTrue(
            any("src/validation_broker/command_registry.py: import failed:" in error for error in errors),
            errors,
        )


def _hook_runtime_import_errors(failing_context: str) -> list[str]:
    original_import_module_result = validator._import_module_result

    def fake_import(path, *args, **kwargs):
        normalized = str(path).replace("\\", "/")
        if normalized.endswith(failing_context):
            return validator.ImportResult(None, "ImportError: forced failure")
        if normalized.endswith("adapters/base.py"):
            return validator.ImportResult(_fake_adapter_module())
        if normalized.endswith("events.py"):
            return validator.ImportResult(
                types.SimpleNamespace(
                    EventKind=[
                        types.SimpleNamespace(value="SessionStart"),
                        types.SimpleNamespace(value="Stop"),
                    ]
                )
            )
        if normalized.endswith("gates.py"):
            return validator.ImportResult(
                types.SimpleNamespace(
                    GateOutcome=[
                        types.SimpleNamespace(value="pass"),
                        types.SimpleNamespace(value="warn"),
                        types.SimpleNamespace(value="block"),
                        types.SimpleNamespace(value="fail_open"),
                        types.SimpleNamespace(value="degraded"),
                    ]
                )
            )
        return original_import_module_result(path, *args, **kwargs)

    validator._import_module_result = fake_import
    try:
        errors: list[str] = []
        warnings: list[str] = []
        validator._validate_hook_runtime_consistency(errors, warnings)
        return errors
    finally:
        validator._import_module_result = original_import_module_result


def _fake_adapter_module():
    def adapter_capabilities_for(_runtime: str):
        return types.SimpleNamespace(supported_events=(), advisory_context_supported=False)

    return types.SimpleNamespace(
        EVENT_KIND_BY_CANONICAL={},
        adapter_capabilities_for=adapter_capabilities_for,
    )


if __name__ == "__main__":
    unittest.main()
