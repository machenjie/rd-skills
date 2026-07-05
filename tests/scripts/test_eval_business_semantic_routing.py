from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCRIPT_PATH = ROOT / "scripts" / "eval-business-semantic-routing.py"
_SPEC = importlib.util.spec_from_file_location("eval_business_semantic_routing_under_test", SCRIPT_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT_PATH}")
ROUTING = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = ROUTING
_SPEC.loader.exec_module(ROUTING)


class BusinessSemanticRoutingEvalTests(unittest.TestCase):
    def test_missing_actual_file_fails(self) -> None:
        rc, output = self._run_eval(_case("missing-actual"), None)

        self.assertNotEqual(rc, 0)
        self.assertIn("missing actual output", output)

    def test_expected_capability_missing_from_actual_fails(self) -> None:
        case = _case("capability-missing", expected_capabilities=["business-semantic-control-plane"])
        actual = _actual("capability-missing", selected_capabilities=["minimal-correct-implementation"])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("missing expected capabilities", output)

    def test_expected_skill_missing_from_actual_fails(self) -> None:
        case = _case("skill-missing", expected_skills=["domain-impact-modeler"])
        actual = _actual("skill-missing", selected_skills=[])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("missing expected skills", output)

    def test_business_semantic_scope_mismatch_fails(self) -> None:
        case = _case("scope-mismatch", business_semantic_scope="expected-scope")
        actual = _actual("scope-mismatch", business_semantic_scope="actual-scope")

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("business_semantic_scope expected", output)

    def test_expected_trigger_missing_from_actual_fails(self) -> None:
        case = _case("trigger-missing", routing_triggers=["business invariant changed"])
        actual = _actual("trigger-missing", detected_triggers=[])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("missing expected detected triggers", output)

    def test_overroute_case_selecting_bsp_fails(self) -> None:
        case = _case("over-routing-simple-local-change", expected_bsp=False, expected_capabilities=["minimal-correct-implementation"])
        actual = _actual(
            "over-routing-simple-local-change",
            business_semantic_pack_required=True,
            selected_capabilities=["business-semantic-control-plane"],
        )

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("overroute selected business-semantic-control-plane", output)

    def test_underroute_case_not_selecting_bsp_fails(self) -> None:
        case = _case(
            "under-routing-high-risk-business-change",
            expected_bsp=True,
            expected_quality_gates=["domain gate", "test gate", "AI review gate"],
        )
        actual = _actual("under-routing-high-risk-business-change", business_semantic_pack_required=False)

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("underroute did not require BSP", output)

    def test_forbidden_skill_selected_fails(self) -> None:
        case = _case("forbidden-skill", forbidden_skills=["domain-impact-modeler"])
        actual = _actual("forbidden-skill", selected_skills=["domain-impact-modeler"])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("forbidden skills selected", output)

    def test_forbidden_capability_selected_fails(self) -> None:
        case = _case("forbidden-capability", forbidden_capabilities=["business-semantic-control-plane"])
        actual = _actual("forbidden-capability", selected_capabilities=["business-semantic-control-plane"])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("forbidden capabilities selected", output)

    def test_max_selected_skills_exceeded_fails(self) -> None:
        case = _case("max-skills", max_selected_skills=1)
        actual = _actual("max-skills", selected_skills=["backend-change-builder", "domain-impact-modeler"])

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("exceeds max_selected_skills", output)

    def test_max_selected_capabilities_exceeded_fails(self) -> None:
        case = _case("max-capabilities", max_selected_capabilities=1)
        actual = _actual(
            "max-capabilities",
            selected_capabilities=["minimal-correct-implementation", "business-semantic-control-plane"],
        )

        rc, output = self._run_eval(case, actual)

        self.assertNotEqual(rc, 0)
        self.assertIn("exceeds max_selected_capabilities", output)

    def test_checked_in_business_semantic_routing_fixtures_pass(self) -> None:
        buffer = io.StringIO()

        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            rc = ROUTING.main()

        self.assertEqual(rc, 0, buffer.getvalue())

    def _run_eval(self, case_yaml: str, actual_yaml: str | None) -> tuple[int, str]:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp_s:
            tmp = Path(tmp_s)
            eval_dir = tmp / "evals" / "business-semantic"
            output_dir = tmp / "evals" / "business-semantic-outputs"
            eval_dir.mkdir(parents=True)
            output_dir.mkdir(parents=True)
            case_id = _case_id(case_yaml)
            (eval_dir / f"{case_id}.yaml").write_text(case_yaml, encoding="utf-8")
            if actual_yaml is not None:
                (output_dir / f"{case_id}.actual.yaml").write_text(actual_yaml, encoding="utf-8")
            old_eval_dir = ROUTING.EVAL_DIR
            old_output_dir = ROUTING.OUTPUT_DIR
            ROUTING.EVAL_DIR = eval_dir
            ROUTING.OUTPUT_DIR = output_dir
            buffer = io.StringIO()
            try:
                with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
                    rc = ROUTING.main()
            finally:
                ROUTING.EVAL_DIR = old_eval_dir
                ROUTING.OUTPUT_DIR = old_output_dir
        return rc, buffer.getvalue()


def _case(
    case_id: str,
    *,
    stage: str = "coding",
    expected_bsp: bool = False,
    business_semantic_scope: str = "none",
    routing_triggers: list[str] | None = None,
    expected_skills: list[str] | None = None,
    expected_capabilities: list[str] | None = None,
    expected_quality_gates: list[str] | None = None,
    expected_bsp_sections: list[str] | None = None,
    forbidden_skills: list[str] | None = None,
    forbidden_capabilities: list[str] | None = None,
    max_selected_skills: int | None = None,
    max_selected_capabilities: int | None = None,
    allow_broad_route: bool | None = None,
) -> str:
    triggers = routing_triggers or []
    skills = expected_skills or []
    capabilities = expected_capabilities or ["minimal-correct-implementation"]
    gates = expected_quality_gates or ["implementation gate"]
    sections = expected_bsp_sections or []
    extras = []
    if forbidden_skills is not None:
        extras.append(f"forbidden_skills: {forbidden_skills}")
    if forbidden_capabilities is not None:
        extras.append(f"forbidden_capabilities: {forbidden_capabilities}")
    if max_selected_skills is not None:
        extras.append(f"max_selected_skills: {max_selected_skills}")
    if max_selected_capabilities is not None:
        extras.append(f"max_selected_capabilities: {max_selected_capabilities}")
    if allow_broad_route is not None:
        extras.append(f"allow_broad_route: {str(allow_broad_route).lower()}")
    extras_text = "\n".join(extras)
    if extras_text:
        extras_text += "\n"
    return f"""case_id: {case_id}
routing_triggers: {triggers}
expected_route:
  stage: {stage}
  business_semantic_pack_required: {str(expected_bsp).lower()}
  business_semantic_scope: {business_semantic_scope}
expected_skills: {skills}
expected_capabilities: {capabilities}
expected_quality_gates: {gates}
expected_bsp_sections: {sections}
{extras_text}
"""


def _actual(
    case_id: str,
    *,
    stage: str = "coding",
    business_semantic_pack_required: bool = False,
    business_semantic_scope: str = "none",
    detected_triggers: list[str] | None = None,
    selected_skills: list[str] | None = None,
    selected_capabilities: list[str] | None = None,
    required_quality_gates: list[str] | None = None,
) -> str:
    triggers = detected_triggers or []
    skills = selected_skills or []
    capabilities = selected_capabilities or ["minimal-correct-implementation"]
    gates = required_quality_gates or ["implementation gate"]
    return f"""actual_metadata:
  generated_by: scripts/generate-business-semantic-actuals.py
  generation_mode: deterministic
  source_fixture: evals/business-semantic/{case_id}.yaml
  route_source: current deterministic route resolver / fixture route adapter
  review_source: deterministic source/diff/prompt/trigger review skeleton
actual_route:
  stage: {stage}
  detected_triggers: {triggers}
  selected_skills: {skills}
  selected_capabilities: {capabilities}
  required_quality_gates: {gates}
  business_semantic_pack_required: {str(business_semantic_pack_required).lower()}
  business_semantic_scope: {business_semantic_scope}
  selected_bsp_sections: []
  selected_references: []
  skipped_references: []
actual_review:
  findings: []
"""


def _case_id(case_yaml: str) -> str:
    return next(line.split(":", 1)[1].strip() for line in case_yaml.splitlines() if line.startswith("case_id:"))


if __name__ == "__main__":
    unittest.main()
