# Agent Behavior Evals

This directory holds **offline** agent-behavior evaluations. Each sample captures
a real (human-reviewed) ChangeForge agent output and the expectations it should
satisfy. The eval validates the captured output; it never calls a model and never
reaches the network.

```
evals/agent-behavior/
  README.md
  professional-samples/ # professional behavior samples grouped by area
  samples/    # human-authored or human-approved candidate samples
  outputs/    # generated eval reports (git-ignored working area)
  promoted/   # human-approved samples locked in as regression guards
```

## What it checks

`scripts/eval-agent-behavior.py` parses the `changeforge_route` manifest from each
sample's captured output and scores it against the sample's `expected` block:

- route manifest is present;
- `selected_skills` covers `expected.selected_skills` and avoids `forbidden_skills`;
- `selected_capabilities` covers `expected.selected_capabilities`;
- `required_references` covers `expected.required_references` and includes the four
  router self-use references;
- every `expected.required_quality_gates` entry is either required or skipped with a
  reason;
- validation evidence and residual risk are present;
- when `expected.runtime_prompt_flow.required` is true, the manifest carries
  closure mode, clarification status, inspected boundaries, TDD signal, action
  owner/review mapping, repair/re-review requirements, validation evidence, and
  residual risk. `plan` may carry pending re-review and planned validation;
  `action-handoff` and `final-handoff` require concrete re-review and validation
  closure states.

It reports `route_recall`, `route_precision`, `capability_recall`,
`reference_adherence`, `gate_closure`, `validation_evidence_score`, runtime flow
scores, and stage projection scores.

## Sample format

```yaml
id: example-behavior-case
description: One-line description.
prompt: The request the agent handled.
expected:
  selected_skills:
    - backend-change-builder
  forbidden_skills:
    - frontend-change-builder
  selected_capabilities:
    - implementation-structure-design
  required_references:
    - references/routing-rules.md
  required_quality_gates:
    - security gate
  runtime_prompt_flow:
    required: true
    closure_mode: plan
    clarification_status: clarified-with-assumptions
    required_inspected_boundaries:
      - files
      - tests
    required_actions:
      - update-backend-handler
    require_owner_review_distinct: true
    require_repair_route: true
    require_re_review_result: true
    require_validation_evidence: true
    require_residual_risk: true
actual:
  # Preferred: the parsed manifest captured from a real session.
  route_manifest:
    schema_version: 1
    selected_skills:
      - backend-change-builder
    selected_capabilities:
      - implementation-structure-design
    required_references:
      - references/routing-rules.md
    required_quality_gates:
      - security gate
    runtime_prompt_flow:
      schema_version: 1
      closure_mode: plan
      clarification_status:
        status: clarified-with-assumptions
      inspected_boundaries:
        files:
          - src/orders/api.py
        tests:
          - tests/test_orders.py
      tdd_signal:
        kind: updated-test
        command_or_check: pytest tests/test_orders.py -q
        expected_evidence: order authorization regression passes
      actions:
        - id: update-backend-handler
          owner_skill: backend-change-builder
          review_skill: quality-test-gate
          review_evidence: regression and authorization cases pass
          repair_route_if_review_fails: backend-change-builder
          re_review_required: true
          re_review_result: pending
      validation_evidence:
        - command: pytest tests/test_orders.py -q
          outcome: planned
      residual_risk:
        - risk: target runtime still needs actual project verification
    skipped_quality_gates:
      - gate: delivery gate
        reason: no deployment change in scope
  # Alternative: raw_output containing a fenced ```yaml changeforge_route block.
  validation_evidence: true
  residual_risk: true
```

Provide either `actual.route_manifest` (already parsed) or `actual.raw_output`
(the agent's markdown including the fenced `changeforge_route` block).

## Run

```bash
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-agent-behavior.py --samples-dir evals/agent-behavior/samples --format markdown
```

With no samples the eval prints `no samples found` and exits 0.

## Professional Samples

`professional-samples/` stores real or realistic agent outputs for professional
behavior regression. These are not showcase examples. They check whether the
captured output selected the expected skills/capabilities/references/gates,
named inspected boundaries, supplied validation evidence or a not-verified
disclosure, stated residual risk, named the next gate, and avoided forbidden
behaviors.

Run:

```bash
python3 scripts/eval-professional-agent-samples.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-professional-agent-samples.py --candidates-only --format json
```

Reports are written to `reports/professional-agent-samples-report.md` and
`reports/professional-agent-samples-report.json`. Default mode is warning-only;
`--strict` is for release checks.

## Promotion

Samples reach this directory only through human review. Telemetry-derived
candidates are generated by `scripts/promote-telemetry-suggestion.py` into
`samples/`; a human reviews, corrects, and moves the locked-in cases into
`promoted/`. No tool auto-promotes a sample.
