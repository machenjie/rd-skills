from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-examples.py"


def _load_module():
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("validate_examples", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ValidateExamplesTests(unittest.TestCase):
    def test_repository_examples_validate(self) -> None:
        module = _load_module()
        self.assertEqual(module.validate_examples(ROOT), [])

    def test_unknown_capability_is_reported(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "src" / "registry").mkdir(parents=True)
            (root / "src" / "registry" / "skills.yaml").write_text(
                "skills:\n  - name: backend-change-builder\n    path: src/professional-skills/backend-change-builder\n",
                encoding="utf-8",
            )
            (root / "src" / "registry" / "domain-extensions.yaml").write_text(
                "domain_extensions: []\n",
                encoding="utf-8",
            )
            (root / "src" / "registry" / "capabilities.yaml").write_text(
                "capabilities:\n  - name: regression-testing\n    path: src/foundation/capabilities/regression-testing\n",
                encoding="utf-8",
            )
            (root / "src" / "registry" / "routing-rules.yaml").write_text(
                "quality_gates:\n  - test gate\n",
                encoding="utf-8",
            )
            scenario = root / "examples" / "01-sample"
            scenario.mkdir(parents=True)
            (root / "examples" / "README.md").write_text("# Examples\n", encoding="utf-8")
            (scenario / "prompt.md").write_text("Change a backend permission path.\n", encoding="utf-8")
            (scenario / "expected-route.md").write_text(
                "```yaml\n"
                "scenario_id: sample-routing-case\n"
                "selected_skills:\n"
                "  - backend-change-builder\n"
                "selected_capabilities:\n"
                "  - invented-capability\n"
                "required_quality_gates:\n"
                "  - test gate\n"
                "```\n",
                encoding="utf-8",
            )
            (scenario / "expected-evidence.md").write_text(
                "read before plan\nTDD\nvalidation evidence\nindependent review\nresidual risk\nhandoff\n",
                encoding="utf-8",
            )
            errors = module.validate_examples(root)
        self.assertTrue(any("unknown capability" in error for error in errors))

    def test_missing_scenario_id_is_reported(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_minimal_registry(root)
            scenario = _write_minimal_scenario(root, "01-sample", "")
            (scenario / "expected-route.md").write_text(
                "```yaml\n"
                "selected_skills:\n"
                "  - backend-change-builder\n"
                "selected_capabilities:\n"
                "  - regression-testing\n"
                "required_quality_gates:\n"
                "  - test gate\n"
                "```\n",
                encoding="utf-8",
            )
            errors = module.validate_examples(root)
        self.assertTrue(any("missing scenario_id" in error for error in errors))

    def test_scenario_route_must_overlap_routing_fixture(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_minimal_registry(root)
            _write_minimal_scenario(root, "01-sample", "fixture-case")
            fixture = root / "evals" / "routing" / "fixture-case.yaml"
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                "---\n"
                "id: fixture-case\n"
                "expected:\n"
                "  skills:\n"
                "    - frontend-change-builder\n"
                "  capabilities:\n"
                "    - frontend-testing\n"
                "  quality_gates:\n"
                "    - implementation gate\n",
                encoding="utf-8",
            )
            errors = module.validate_examples(root)
        self.assertTrue(any("has no selected_skills overlap" in error for error in errors))

    def test_scenario_route_must_not_overlap_fixture_forbidden(self) -> None:
        module = _load_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_minimal_registry(root)
            scenario = _write_minimal_scenario(root, "01-sample", "fixture-case")
            fixture = root / "evals" / "routing" / "fixture-case.yaml"
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                "---\n"
                "id: fixture-case\n"
                "expected:\n"
                "  skills:\n"
                "    - backend-change-builder\n"
                "  capabilities:\n"
                "    - regression-testing\n"
                "  quality_gates:\n"
                "    - test gate\n"
                "forbidden:\n"
                "  skills:\n"
                "    - frontend-change-builder\n"
                "  capabilities:\n"
                "    - release-rollback\n"
                "  quality_gates:\n"
                "    - delivery gate\n",
                encoding="utf-8",
            )
            # Regression: routes can overlap fixture expected values and still
            # be invalid when they select forbidden values.
            (scenario / "expected-route.md").write_text(
                "```yaml\n"
                "scenario_id: fixture-case\n"
                "selected_skills:\n"
                "  - backend-change-builder\n"
                "  - frontend-change-builder\n"
                "selected_capabilities:\n"
                "  - regression-testing\n"
                "  - release-rollback\n"
                "required_quality_gates:\n"
                "  - test gate\n"
                "  - delivery gate\n"
                "```\n",
                encoding="utf-8",
            )
            errors = module.validate_examples(root)
        expected_conflicts = (
            "selected_skills conflicts with routing fixture forbidden",
            "selected_capabilities conflicts with routing fixture forbidden",
            "required_quality_gates conflicts with routing fixture forbidden",
        )
        for expected in expected_conflicts:
            self.assertTrue(any(expected in error for error in errors))


def _write_minimal_registry(root: Path) -> None:
    (root / "src" / "registry").mkdir(parents=True)
    (root / "src" / "registry" / "skills.yaml").write_text(
        "skills:\n"
        "  - name: backend-change-builder\n"
        "    path: src/professional-skills/backend-change-builder\n"
        "  - name: frontend-change-builder\n"
        "    path: src/professional-skills/frontend-change-builder\n",
        encoding="utf-8",
    )
    (root / "src" / "registry" / "domain-extensions.yaml").write_text(
        "domain_extensions: []\n",
        encoding="utf-8",
    )
    (root / "src" / "registry" / "capabilities.yaml").write_text(
        "capabilities:\n"
        "  - name: regression-testing\n"
        "    path: src/foundation/capabilities/regression-testing\n"
        "  - name: frontend-testing\n"
        "    path: src/foundation/capabilities/frontend-testing\n"
        "  - name: release-rollback\n"
        "    path: src/foundation/capabilities/release-rollback\n",
        encoding="utf-8",
    )
    (root / "src" / "registry" / "routing-rules.yaml").write_text(
        "quality_gates:\n"
        "  - test gate\n"
        "  - implementation gate\n"
        "  - delivery gate\n",
        encoding="utf-8",
    )


def _write_minimal_scenario(root: Path, name: str, scenario_id: str) -> Path:
    scenario = root / "examples" / name
    scenario.mkdir(parents=True)
    (root / "examples" / "README.md").write_text("# Examples\n", encoding="utf-8")
    (scenario / "prompt.md").write_text("Change a backend path.\n", encoding="utf-8")
    route_prefix = f"scenario_id: {scenario_id}\n" if scenario_id else ""
    (scenario / "expected-route.md").write_text(
        "```yaml\n"
        f"{route_prefix}"
        "selected_skills:\n"
        "  - backend-change-builder\n"
        "selected_capabilities:\n"
        "  - regression-testing\n"
        "required_quality_gates:\n"
        "  - test gate\n"
        "```\n",
        encoding="utf-8",
    )
    (scenario / "expected-evidence.md").write_text(
        "read before plan\nTDD\nvalidation evidence\nindependent review\nresidual risk\nhandoff\n",
        encoding="utf-8",
    )
    return scenario


if __name__ == "__main__":
    unittest.main()
