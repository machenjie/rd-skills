# Task DAG Contract v2

Use only for at least two real tasks with an evidenced dependency, parallel
benefit, cross-owner boundary, integration need, or migration/release order.

For Analyzed Work, this DAG is a derived projection of the current Engineering
Brief. It may split Brief work, project Task Contracts, dependencies, parallel
safety, critical path, and integration, merge, and conflict ownership. It must
not select or replace the First Executable Slice or modify Acceptance,
Non-goals, Owner, Invariants, Placement, contract semantics, or Rollback.
The First Executable Slice below names the Brief-selected Task ID; its matching
task node is a verbatim projection, and Main dispatches the Brief slice itself.
If the Brief is insufficient or any projection conflicts with it, mark the DAG
blocked and return to analysis through Main for an updated Brief and redispatch.

Each Task is one complete semantic change with one Primary Professional Skill.
Keep co-effective changes for one Acceptance together when they naturally
validate together. Split materially different professional domains into
separate Tasks. File, function, code layer, test, or edit step differences do
not define Tasks. Define minimum sufficient Review Boundaries. Related work is
combined by default. Concrete risk justifies an intermediate boundary. Combined
review preserves Primary Skills, required Review Skills, Specialists, and
professional-risk obligations. Review-side Layer 3 is selected independently
from review risk and is not copied from Task implementation Layer 3.

The public Execution Level lines use Core public `execution-level/v2`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy v1 is completed/read only; active or resumed work, edit,
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
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
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
Required Review Skills:
Specialist Obligations:
Professional Risk Dimensions:

## Task B

Task ID:
Status: in_progress
<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: task-dag-template.md -->
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
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
Required Review Skills:
Specialist Obligations:
Professional Risk Dimensions:

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

Review Owner:
Review Boundary ID:
Review Strategy: combined-final / risk-triggered-intermediate:<Core trigger> / L5-preimplementation / L5-final
Review Round ID:
Effective Level:
Required Review Skills:
Specialist Obligations:
Covered Task IDs:
Required Changed Scope:
Professional Risk Dimensions:
Required Validation / Evidence Binding:
Review Assignments: one primary and zero or more specialists; each has Assignment ID, role, review-agent profile, exactly one Review Skill, zero to three review-risk-routed Layer 3 Skills, selection basis, and bounded scope
Primary Close Ordering: every required specialist result is current before the primary emits the sole combined artifact

Task nodes retain only review requirements; Review strategy, round identity,
assignment scheduling, and primary-close ordering live here. All assignments
in a boundary share one Review Round ID. Specialist results neither increment
the round count nor close Tasks. The primary consumes every current required
specialist result and emits one artifact binding the boundary, covered Tasks,
required changed and evidence scope, current Task generations, assignment
results, and verdict. Each covered Task projects that exact artifact identity
and digest. L1-L3 related work defaults to one combined independent final
review. L4 adds only triggered professional depth, not review rounds. L5
retains required independent pre-implementation and final review. An
equivalent per-Task boundary is invalid without a declared Core intermediate
trigger, and one stronger boundary subsumes weaker equivalent obligations.
Review-side Layer 3 is selected independently per assignment from
review risk and need not equal or contain the Tasks' implementation Layer 3.

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
