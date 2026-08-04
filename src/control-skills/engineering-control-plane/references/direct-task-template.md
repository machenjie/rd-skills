# Direct Task Contract v2

Direct Task requires explicit behavior, local scope, owner, observable
acceptance, non-production verification, placement, and rollback; work is
low-risk, reversible, and clear of excluded boundaries or unresolved material
impact. Otherwise route to Analyzed Work.

Inspect within named owner, test, and consumer boundaries. If ownership or
verification needs discovery, stop and route to Analyzed Work. Use `not
applicable` for a field that has no Direct Task value.

The public Execution Level lines use Core public `execution-level/v1`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy without v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Direct Task Contract v2

## Task ID

## Status

in_progress

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: direct-task-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: direct-task-template.md -->

## Goal

## Owner

## Inputs

## Allowed Read Scope

## Allowed Write Scope

## Inspection Boundary

Name the already known owner, test, and consumer boundaries that inspection may
confirm.

## Inspection Stop Conditions

Stop before editing and return to Analyzed Work when owner, placement, behavior,
verification, rollback, material impact, or risk leaves the declared boundary.

## Non-goals

## Expected Output

## Acceptance

## Verification

## Evidence Requirements

Name the claims, commands, artifacts, freshness requirement, scope, and proof
limits that must appear in the task-local Evidence Ledger.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.

## Parallel Safety

## Workspace Requirement

## Integration Owner

Write `not applicable` when no integration occurs.

## Review Owner

## Stop Conditions

## Professional Skill

Primary:
Layer 3 (only triggered items):
Review:
```

Do not add private runtime state, a hidden protocol record, or a Task DAG.
