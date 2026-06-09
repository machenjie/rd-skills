# ChangeForge Pressure Scenarios

Pressure scenarios capture the realistic excuses an agent reaches for to skip a
discipline rule, paired with the behavior the rule must still enforce. They are
the behavior-evidence layer behind discipline-enforcing skills: a rule that only
holds on the cooperative path is not enforced.

`scripts/eval-pressure-behavior.py` reads every `*.yaml` under this tree, except
`outputs/`. It never calls a model and never reaches the network. With no
scenarios it prints `no samples found` and exits 0.

## Areas

- `routing/` — skipping the router, or over-routing a trivial change.
- `implementation-structure/` — new structure without a reuse ladder or placement.
- `completion-evidence/` — completion claims without fresh validation evidence.
- `skill-authoring/` — skill edits without baseline failure, over-routing guards,
  or that drift into description-as-workflow.
- `two-stage-review/` — code-quality approval before spec compliance.
- `planning/` — placeholder plans and tasks without a validation command.

## Scenario Fields

- `id`, `pressure_type`, `prompt` — required.
- `expected_route` (`skills`, `capabilities`, `stage`) — the path the change must
  hold under pressure.
- `required_capabilities`, `required_evidence`, `forbidden_behaviors`,
  `rationalizations_to_reject`, `completion_claim_allowed`,
  `expected_handoff_fields` — the spec the agent result must satisfy.
- `captured` (optional) — a human-reviewed agent result to score. A scenario
  without `captured` is a defined-but-unsampled spec: it is schema-validated but
  not scored, so a real agent sample can be added later.

A `captured` block carries `selected_skills`, `selected_capabilities`,
`validation_evidence`, `residual_risk`, `completion_claim`, `handoff_fields`, and
`observed_behaviors`. The runner fails a scored scenario when a forbidden behavior
or rejected rationalization appears, when a completion claim is disallowed or
lacks validation evidence, or when registry names are unknown.

Captured samples are regression guards: they record the correct behavior under
pressure, so they pass. They are promoted only by a human; see
[../../docs/TELEMETRY.md](../../docs/TELEMETRY.md).
