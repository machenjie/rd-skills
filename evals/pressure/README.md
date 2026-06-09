# ChangeForge Pressure Scenarios

Pressure scenarios capture the realistic excuses an agent reaches for to skip a
discipline rule, paired with the behavior the rule must still enforce. They are
the behavior-evidence layer behind discipline-enforcing skills: a rule that only
holds on the cooperative path is not enforced.

`scripts/eval-pressure-behavior.py` reads every `*.yaml` under this tree, except
`outputs/`. It never calls a model and never reaches the network. With no
scenarios it prints `no samples found` and exits 0.

Committed scenarios are formal eval inputs: required lists must be non-empty,
`expected_route.skills` and `expected_route.capabilities` must be non-empty, and
TODO placeholders are treated as incomplete. Telemetry-promoted skeletons may be
checked separately with `--allow-todo-candidates` while they are still unfinished
candidates; do not use that flag for this committed tree.

## Areas

- `routing/` — skipping the router, or over-routing a trivial change.
- `implementation-structure/` — new structure without a reuse ladder or placement.
- `completion-evidence/` — completion claims without fresh validation evidence.
- `skill-authoring/` — skill edits without baseline failure, over-routing guards,
  or that drift into description-as-workflow.
- `two-stage-review/` — code-quality approval before spec compliance.
- `planning/` — placeholder plans and tasks without a validation command.

## Scenario Fields

- `id`, `pressure_type`, `prompt` — required non-empty strings.
- `expected_route` (`skills`, `capabilities`, optional `stage`) — the path the
  change must hold under pressure. `skills` and `capabilities` are required
  non-empty lists.
- `required_capabilities`, `required_evidence`, `forbidden_behaviors`,
  `rationalizations_to_reject`, `completion_claim_allowed`,
  `expected_handoff_fields` — the spec the agent result must satisfy. Required
  lists are non-empty in formal scenarios.
- `captured` (optional) — a human-reviewed agent result to score. A scenario
  without `captured` is a defined-but-unsampled spec: it is schema-validated but
  not scored, so a real agent sample can be added later.

A `captured` block carries `selected_skills`, `selected_capabilities`,
`validation_evidence`, `residual_risk`, `completion_claim`, `handoff_fields`, and
`observed_behaviors`. The runner fails a scored scenario when a forbidden behavior
or rejected rationalization appears, when a completion claim is disallowed or
lacks validation evidence, when `expected_route.skills` or
`expected_route.capabilities` are missing from the captured route, when a
captured stage conflicts with `expected_route.stage`, or when registry names or
required-evidence tokens are unknown. Reports include `skill_coverage`,
`route_coverage`, `capability_coverage`, `evidence_coverage`, and
`handoff_coverage`.

Captured samples are regression guards: they record the correct behavior under
pressure, so they pass. They are promoted only by a human; see
[../../docs/TELEMETRY.md](../../docs/TELEMETRY.md).
