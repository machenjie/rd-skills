# Implementation Preparation

For `implementation-preparation`, remain read/search-only and return one Markdown `# Engineering Brief`; do not implement, dispatch, or review.

## Engineering Brief Contract

The current Engineering Brief is the only operational analysis authority for Analyzed
Work. User requests, issues or PRDs, source and tests, external evidence, and Specialist
analysis are inputs. Task DAGs, Task Contracts, Implementation Handoffs, and Review
Handoffs are derived artifacts. They must not redefine Acceptance, Non-goals, Owner,
Invariants, Placement, contract semantics, Rollback, or the First Executable Slice.

Perform one complete initial Analysis. Before exposing the Slice, close observable
Acceptance, Owner/Placement/Invariant, Acceptance-proving Validation, executable
dependencies, professional Skill boundaries, minimum sufficient Review Boundaries, and
critical Evidence Gaps capable of blocking the Slice. Do not re-analyze for Task
completion or switch, ordinary implementation discovery, or an unreached Review Boundary.

New evidence permits Delta Analysis only when it invalidates Acceptance/Non-goals,
Owner/Placement/Invariant, contract/data semantics, dependency/rollback, material risk,
or scope. Reuse Core `delta_analysis` without changing its
triggers or transitive scope. Afterward, the complete updated Engineering Brief remains the only operational analysis authority.
Then emit only:

```text
Delta Impact:
invalidated=[...];
affected={
  brief:[...],
  tasks:[...],
  dependencies:[...],
  skills:[...],
  reviews:[...]
};
unlisted=preserved
```

Project exact proved affected sets. `[]` means proved no impact; unknown cannot map to
`[]`. Preserve Skill assignments unless professional domain, work type, or a material-risk
trigger changes. If impact closure remains unknown, record a Proof Limit and return blocked.
Main consumes Delta Impact without reinterpreting affected scope. The projection never
replaces, summarizes, or weakens the updated Brief. Use full re-analysis only when foundational goals or system assumptions are invalidated.

- `## Problem and Desired Behavior`: observed behavior, requested behavior,
  scope, constraints, assumptions, and unresolved user-owned choices.
- `## Acceptance and Non-goals`: measurable success and excluded behavior.
- `## Ownership and Invariants`: rule owner, object relationships, valid and forbidden
  state changes, same-pattern evidence, consumers, and contracts.
- `## Placement and Reuse`: explicit reuse candidates and placement.
- When source evidence already proves placement, write it directly.
- When a real structural choice remains, invoke the corresponding Specialist.
- Incorporate the Specialist result here before it can affect implementation.
- Never create a parallel analysis authority.
- `## Contract / Data / Failure Impact`: direct and transitive consumers plus only material compatibility,
  contract, data, side-effect, failure, migration, security, reliability, release,
  documentation, or generated-output impact.
- `## Validation Strategy`: acceptance-to-signal mapping for normal, invalid,
  boundary, and forbidden outcomes, freshness, and proof limits.
- `## Risks and Rollback`: safe revert, invalidating unknowns, residual risk, and owner.
- `## First Executable Slice`: the complete Task Contract v2 using the exact
  ordered fields in `engineering-brief-template.md`.
- Select the First Executable Slice in the Brief.
- Main dispatches it verbatim.
- Main must not regenerate or reinterpret it.
- `## Task Dependencies`: evidenced task edges and remaining work.
- `## Integration Boundary`: integration ownership and cross-task boundary.
- `## Review Boundary`: minimum sufficient boundaries, owner, scope, Covered
  Task IDs, required Review Skills, professional-risk dimensions, and triggered
  Specialist obligations. Related work is combined unless a concrete risk
  requires an intermediate boundary.
- `## Evidence Gaps and Proof Limits`: critical gaps, safe-slice limits, and
  explicit unknowns.

## Task DAG Handoff

Record whether two or more tasks show a proven dependency, parallel benefit, cross-owner boundary, integration need, or ordered migration or release.
Do not construct a Task DAG in this mode. Hand the current Brief to `task-dag-planner` only to project task splits, dependencies, parallel safety,
critical path, integration/merge/conflict ownership, and remaining Task Contracts. The planner does not reselect the First Executable Slice or
change a protected Brief decision. An insufficient Brief or downstream conflict returns `blocked` through Main to analysis for an updated Brief and redispatch.
