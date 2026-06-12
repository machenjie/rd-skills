from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVAL_SCRIPT = ROOT / "scripts" / "eval-agent-behavior.py"

PASSING_SAMPLE = """id: sample-pass
description: passing sample
prompt: do a backend auth fix
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills:
    - frontend-change-builder
  selected_capabilities:
    - authentication-authorization
  required_references:
    - references/routing-rules.md
  required_quality_gates:
    - security gate
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - security-privacy-gate
  selected_capabilities:
    - authentication-authorization
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates:
    - security gate
  skipped_quality_gates:
    - delivery gate => no deployment change
"""

FORBIDDEN_SAMPLE = """id: sample-forbidden
description: forbidden skill present
prompt: do something
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills:
    - frontend-change-builder
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - frontend-change-builder
  selected_capabilities: []
  selected_domain_extensions: []
  required_references: []
  required_quality_gates: []
  skipped_quality_gates: []
"""

MISSING_SELF_REF_SAMPLE = """id: sample-missing-self-ref
description: manifest omits router self-use references
prompt: do something
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills: []
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
  selected_capabilities: []
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
  required_quality_gates: []
  skipped_quality_gates: []
"""

STAGE_MISSING_SAMPLE = """id: sample-stage-missing
description: declares a stage expectation but emits no stage manifest
prompt: do a multi-file backend change
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills: []
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
  expected_stage: coding
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
  selected_capabilities: []
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates: []
  skipped_quality_gates: []
"""

PLAN_RUNTIME_FLOW_SAMPLE = """id: sample-plan-runtime-flow
description: plan closure may carry pending re-review and planned validation
prompt: plan a backend change
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  forbidden_skills: []
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
  runtime_prompt_flow:
    required: true
    closure_mode: plan
    clarification_status: clarified
    required_inspected_boundaries:
      - files
    required_actions:
      - update-handler
    require_owner_review_distinct: true
    require_repair_route: true
    require_re_review_result: true
    require_validation_evidence: true
    require_residual_risk: true
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  selected_capabilities: []
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates: []
  skipped_quality_gates: []
  runtime_prompt_flow:
    schema_version: 1
    closure_mode: plan
    clarification_status:
      status: clarified
    inspected_boundaries:
      files:
        - src/orders/api.py
    tdd_signal:
      kind: validation-command
      command_or_check: pytest tests/test_orders.py -q
    actions:
      - id: update-handler
        owner_skill: backend-change-builder
        review_skill: quality-test-gate
        review_evidence: reviewer will inspect the planned test result
        repair_route_if_review_fails: backend-change-builder
        re_review_required: true
        re_review_result: pending
    validation_evidence:
      - command: pytest tests/test_orders.py -q
        outcome: planned
    residual_risk:
      - risk: implementation has not run yet
        owner: next agent
        next_gate: action-handoff
"""

ACTION_PENDING_REREVIEW_SAMPLE = """id: sample-action-pending-rereview
description: action handoff may not close with pending re-review
prompt: implement a backend change
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  forbidden_skills: []
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
  runtime_prompt_flow:
    required: true
    closure_mode: action-handoff
    clarification_status: clarified
    required_inspected_boundaries:
      - files
    required_actions:
      - update-handler
    require_owner_review_distinct: true
    require_repair_route: true
    require_re_review_result: true
    require_validation_evidence: true
    require_residual_risk: true
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  selected_capabilities: []
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates: []
  skipped_quality_gates: []
  runtime_prompt_flow:
    schema_version: 1
    closure_mode: action-handoff
    clarification_status:
      status: clarified
    inspected_boundaries:
      files:
        - src/orders/api.py
    tdd_signal:
      kind: validation-command
      command_or_check: pytest tests/test_orders.py -q
    actions:
      - id: update-handler
        owner_skill: backend-change-builder
        review_skill: quality-test-gate
        review_evidence: regression test result
        repair_route_if_review_fails: backend-change-builder
        re_review_required: true
        re_review_result: pending
    validation_evidence:
      - command: pytest tests/test_orders.py -q
        outcome: passed
    residual_risk:
      - risk: fixture project only
        owner: next agent
        next_gate: closed
"""

FINAL_PLANNED_VALIDATION_SAMPLE = """id: sample-final-planned-validation
description: final handoff may not close with validation evidence that is only planned
prompt: finish a backend change
validation_evidence: true
residual_risk: true
expected:
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  forbidden_skills: []
  selected_capabilities: []
  required_references: []
  required_quality_gates: []
  runtime_prompt_flow:
    required: true
    closure_mode: final-handoff
    clarification_status: clarified
    required_inspected_boundaries:
      - files
    required_actions:
      - update-handler
    require_owner_review_distinct: true
    require_repair_route: true
    require_re_review_result: true
    require_validation_evidence: true
    require_residual_risk: true
manifest:
  schema_version: 1
  selected_skills:
    - backend-change-builder
    - quality-test-gate
  selected_capabilities: []
  selected_domain_extensions: []
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
  required_quality_gates: []
  skipped_quality_gates: []
  runtime_prompt_flow:
    schema_version: 1
    closure_mode: final-handoff
    clarification_status:
      status: clarified
    inspected_boundaries:
      files:
        - src/orders/api.py
    tdd_signal:
      kind: validation-command
      command_or_check: pytest tests/test_orders.py -q
    actions:
      - id: update-handler
        owner_skill: backend-change-builder
        review_skill: quality-test-gate
        review_evidence: regression test result
        repair_route_if_review_fails: backend-change-builder
        re_review_required: true
        re_review_result: passed
    validation_evidence:
      - command: pytest tests/test_orders.py -q
        outcome: planned
    residual_risk:
      - risk: fixture project only
        owner: next agent
        next_gate: closed
"""


def _run(samples_dir: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    return subprocess.run(
        [
            sys.executable,
            str(EVAL_SCRIPT),
            "--samples-dir",
            str(samples_dir),
            "--output-dir",
            str(output_dir),
            "--format",
            "json",
        ],
        text=True,
        capture_output=True,
        cwd=str(ROOT),
        env=env,
        check=False,
    )


class EvalAgentBehaviorTests(unittest.TestCase):
    def test_no_samples_found_returns_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no samples found", result.stdout)

    def test_passing_sample_scores_high(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "pass.yaml").write_text(PASSING_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("route_recall=1.00", result.stdout)
        self.assertIn("gate_closure=1.00", result.stdout)

    def test_forbidden_skill_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "forbidden.yaml").write_text(FORBIDDEN_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 1)
        self.assertIn("forbidden", result.stderr)

    def test_committed_samples_pass(self) -> None:
        # The repository's own samples must remain valid for the standard
        # validation workflow.
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(EVAL_SCRIPT), "--output-dir", str(tmp)],
                text=True,
                capture_output=True,
                cwd=str(ROOT),
                env=os.environ.copy(),
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_missing_self_references_is_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "sr.yaml").write_text(MISSING_SELF_REF_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 1)
        self.assertIn("self-use reference", result.stderr)

    def test_declared_stage_without_manifest_scores_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "sm.yaml").write_text(STAGE_MISSING_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stage_presence=0.00", result.stdout)

    def test_plan_closure_allows_pending_rereview_and_planned_validation(self) -> None:
        # Regression: planning output can name future review and validation work without closing it.
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "plan.yaml").write_text(PLAN_RUNTIME_FLOW_SAMPLE, encoding="utf-8")
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("runtime_repair_rereview=1.00", result.stdout)
        self.assertIn("runtime_validation_residual=1.00", result.stdout)

    def test_action_handoff_rejects_pending_rereview(self) -> None:
        # Regression: action handoff must not treat pending re-review as completed review evidence.
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "action.yaml").write_text(
                ACTION_PENDING_REREVIEW_SAMPLE,
                encoding="utf-8",
            )
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 1)
        self.assertIn("re_review_result", result.stderr)

    def test_final_handoff_rejects_planned_only_validation(self) -> None:
        # Regression: final handoff needs actual validation outcome or an explicit non-verified disclosure.
        with tempfile.TemporaryDirectory() as tmp:
            samples = Path(tmp) / "samples"
            samples.mkdir()
            (samples / "final.yaml").write_text(
                FINAL_PLANNED_VALIDATION_SAMPLE,
                encoding="utf-8",
            )
            result = _run(samples, Path(tmp) / "out")
        self.assertEqual(result.returncode, 1)
        self.assertIn("validation_evidence outcome", result.stderr)


if __name__ == "__main__":
    unittest.main()
