# Task DAG Contract v2

Use only for at least two real tasks with an evidenced dependency, parallel
benefit, cross-owner boundary, integration need, or migration/release order.

The public Execution Level lines use Core public `execution-level/v1`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy without v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Task DAG Contract v2

## Status

in_progress / blocked / partial / completed

## First Executable Slice

Task ID:

## Critical Path

## Workspace Requirement

Workspace Mode: shared / isolated / unknown
Write Scheduling Consequence:

## Task A

Task ID:
Status: in_progress
<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: task-dag-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: task-dag-template.md -->
Goal:
Owner:
Inputs:
Allowed Read Scope:
Allowed Write Scope:
Non-goals:
Dependencies:
Expected Output:
Acceptance:
Verification:
Evidence Requirements:
Parallel Safety:
Workspace Requirement:
Integration Owner:
Review Owner:
Stop Conditions:
Professional Skill:
Layer 3 Skills:
Review Strategy: per-task / combined / high-risk-specialized
Review Skill:
Review Scope:
Review Boundary:

## Task B

Task ID:
Status: in_progress
<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: task-dag-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: task-dag-template.md -->
Goal:
Owner:
Inputs:
Allowed Read Scope:
Allowed Write Scope:
Non-goals:
Dependencies:
Expected Output:
Acceptance:
Verification:
Evidence Requirements:
Parallel Safety:
Workspace Requirement:
Integration Owner:
Review Owner:
Stop Conditions:
Professional Skill:
Layer 3 Skills:
Review Strategy: per-task / combined / high-risk-specialized
Review Skill:
Review Scope:
Review Boundary:

## Parallel Group

Parallel Group:
Task IDs:
Workspace Requirement:
Integration Owner:
Merge Owner:
Conflict Resolution Owner:

Omit this group only when no tasks are parallel.

## Integration Boundary

Integration Owner:
Merge Owner:
Conflict Resolution Owner:

## Review Boundary

Primary Review Skill:
Review Owner:
Covered Task IDs:
Changed Scope:
Specialized Secondary Reviews:

Every task belongs to exactly one primary review boundary. A specialized
secondary review names its material risk and does not replace final review.

## Validation Boundary

## Evidence Requirements

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use `current`, `superseded`, or `invalid`. If no graph or dependency evidence
exists, write `none`, state the proof limit, and do not mark the plan `completed`.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.
```

With a shared or unknown workspace, serialize writes. Parallel write tasks
require an isolated workspace, no dependency, and no shared write surface.
Use visible Markdown; do not create a runtime task state engine.
