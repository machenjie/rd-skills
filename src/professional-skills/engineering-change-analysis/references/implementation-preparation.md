# Implementation Preparation

For `implementation-preparation`, remain read/search-only and return one
Markdown `# Engineering Brief`; do not implement, dispatch, or review.

## Engineering Brief Contract

- `## Problem and Desired Behavior`: observed behavior, requested behavior,
  scope, constraints, assumptions, and unresolved user-owned choices.
- `## Acceptance and Non-goals`: measurable success and excluded behavior.
- `## Ownership and Invariants`: rule owner, object relationships, valid and forbidden
  state changes, same-pattern evidence, consumers, and contracts.
- `## Reuse and Structural Risk`: explicit reuse candidates, source-backed module-boundary and dependency-risk evidence, and an explicit placement-decision handoff to `architecture-impact-reviewer`; do not choose or reject a placement or location.
- `## Triggered Impact`: direct and transitive consumers plus only material compatibility,
  contract, data, side-effect, failure, migration, security, reliability, release,
  documentation, or generated-output impact.
- `## Validation Strategy`: acceptance-to-signal mapping, freshness, and proof limits.
- `## Risks and Rollback`: safe revert, invalidating unknowns, residual risk, and owner.
- `## Candidate Task Boundaries and Scheduling Handoff`: non-authoritative candidate boundaries, DAG-trigger evidence, unresolved scheduling constraints, and the post-acceptance handoff to `task-dag-planner`.

## Non-Authoritative Slice Hypothesis

When useful, record an earliest safe, verifiable, reversible slice hypothesis
using `Goal`, `Allowed Scope`, `Acceptance`, `Verify`, `Professional Skill`,
`Layer 3 Skills`, `Review Skill`, and `Stop Conditions`. Label it
non-authoritative and non-dispatchable.

## Task DAG Handoff

Record whether two or more candidate tasks show a proven dependency, parallel
benefit, cross-owner boundary, integration need, or ordered migration or
release. Do not construct a Task DAG in this mode. After the Engineering Brief
is accepted, hand the evidence to `task-dag-planner`; it independently selects
the First Executable Slice and solely emits any authoritative Task DAG or Task
Contract v2.
