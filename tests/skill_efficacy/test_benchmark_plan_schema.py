from __future__ import annotations

import importlib.util
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "validate-skill-efficacy-benchmarks.py"
SCRIPTS_DIR = ROOT / "scripts"


def _load_validator() -> ModuleType:
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location("validate_skill_efficacy", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("could not import validate-skill-efficacy-benchmarks.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


class BenchmarkPlanSchemaTests(unittest.TestCase):
    def test_existing_benchmarks_validate(self) -> None:
        self.assertEqual(VALIDATOR.main(), 0)

    def test_required_references_are_allow_list_not_all_references(self) -> None:
        errors: list[str] = []
        capabilities = VALIDATOR._load_capability_names(errors)
        self.assertFalse(errors)
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            path = Path(tmp) / "invalid-all-references.yaml"
            path.write_text(
                textwrap.dedent(
                    """
                    id: invalid-all-references
                    capability: skill-efficacy-benchmark
                    task: Validate that all references is rejected.
                    baseline:
                      description: Baseline omits the skill efficacy benchmark plan and can over-read context without explaining the budget.
                      selected_capabilities:
                        - agent-execution-discipline
                      token_cost: not_collected
                      turn_count: not_collected
                    treatment:
                      description: Treatment selects skill efficacy benchmark and records a bounded explicit reference allow-list.
                      selected_capabilities:
                        - skill-efficacy-benchmark
                      token_cost: not_collected
                      turn_count: not_collected
                    metrics:
                      behavior_delta:
                        - Requires explicit benchmark plan evidence.
                        - Rejects unbounded reference selection.
                      token_overhead_pct: not_collected
                      turn_overhead_pct: not_collected
                    skill_efficacy_benchmark:
                      changed_surface: router
                      baseline_case:
                        task: Validate all references handling.
                        expected_current_behavior: Unbounded references may be accepted.
                        known_gap: Context budget cannot be checked.
                      treatment_case:
                        expected_new_behavior: Bounded references are required.
                        selected_skills:
                          - change-forge-router
                        selected_capabilities:
                          - skill-efficacy-benchmark
                        required_references:
                          - all references
                        skipped_references:
                          - reference: src/foundation/capabilities/test-strategy/SKILL.md
                            reason: Not needed for this negative schema case.
                      metrics:
                        over_routing: Unbounded all references is over-routing.
                        under_routing: Missing efficacy benchmark is under-routing.
                        selected_reference_count: 1
                        token_budget_mode: single-stage
                        turn_overhead: not_collected
                        closure_evidence_required: true
                      regression_commands:
                        - python3 scripts/validate-skill-efficacy-benchmarks.py
                      caveats:
                        - Negative schema case.
                    verdict:
                      status: structural_pass
                      rationale: This synthetic fixture is expected to fail schema validation on required_references.
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            VALIDATOR._validate_benchmark(path, capabilities, errors)
        self.assertTrue(
            any("explicit allow-list" in error for error in errors),
            errors,
        )


if __name__ == "__main__":
    unittest.main()
