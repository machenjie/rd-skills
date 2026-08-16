# Subagent and Review Model

Subagents are an internal execution method. A request to implement, repair, diagnose, validate, review, or release authorizes the bounded subagents needed to perform it. Ask the user only for a material behavior/scope decision, destructive or production operation, permission elevation, irreversible data change, or an otherwise unknowable requirement.

## Profiles

| Profile | Tools | Owns | Must not do |
| --- | --- | --- | --- |
| `main-control-agent` | dispatch | classification, path, scheduling, progress, review/repair, closure | inspect code, define acceptance/placement, edit, execute, review |
| `analysis-agent` | read, search | one complete initial Analysis or an invalidated-decision Delta; acceptance, owner, invariants, impact, validation, first slice | edit, dispatch, final review |
| `task-agent` | read, search, edit, execute | one complete semantic implementation or repair Task under one Primary Professional Skill, plus targeted validation | widen scope, global reroute, independent final review |
| `review-agent` | read, search, non-modifying execute | assigned Review/Risk Boundary and actual implementation/repair diff, or a bounded pre-implementation artifact; changed scope, evidence, findings | edit or repair |

## Context Isolation

Give each subagent only the managed task and proof schema projected below. DAG
nodes add `Dependencies`; a Direct Task omits them when they have no meaning.
Do not provide the full conversation, full Task DAG, other tasks, implementer
reasoning, catalogs, or framework internals.

In `recommended` and `full`, the agent opens each capsule-named Layer 3 item
directly at the primary Professional Skill's compiled
`references/layer3/<name>.md` path without opening the index first. In `dev`, it
may load those exact names as top-level Skills. Neither mode permits catalog
preloading.

An accepted Engineering Brief and next executable Task remain authoritative
through Task completion or switching, ordinary implementation discovery, and an
unreached Review Boundary. Only protected-decision invalidation returns through
Main for bounded Delta Analysis of the decision and transitive impact. Skill
assignments are preserved unless professional domain, work type, or material
risk changes.

## Parallelism

Current supported-host projections may run independent read-only investigation
and review concurrently, but all declare isolated workspaces unsupported and
therefore serialize writes. Parallel writes are only a conditional contract for
a future host-provided isolated workspace with verified non-overlap.
Every parallel group names its Integration Owner, Merge Owner, Conflict
Resolution Owner, and workspace requirement.

## Task and Review Scheduling

Task nodes follow complete semantic and Primary Professional Skill boundaries,
not file, function, layer, test, or edit-step boundaries. Work that must jointly
satisfy one Acceptance and naturally validates together stays together, while
materially different professional work remains separate with one Primary Skill
per Task.

Related Tasks inside one Review Boundary execute continuously: each Task Agent
performs targeted validation after its final material edit, then Main dispatches
one combined review at the minimum sufficient Review/Risk Boundary. Task
completion is progress, not an Analysis, Review, replanning, or user-confirmation
trigger. Task, edit, and file counts do not otherwise set Review frequency. An
intermediate review requires concrete public-contract/schema/protocol,
migration/data, security/privacy, transaction/concurrency/persistence,
downstream-rework, independent-integration, L5, or explicit professional-gate
risk.

Task nodes retain required Review Skills, Specialist obligations, and
professional-risk dimensions only. The global Review Boundary owns strategy,
frequency, assignment scheduling, Review Round ID, and primary-close ordering.
It creates one primary and zero or more specialist review-agent assignments;
each assignment has one ID, role, exactly one Review Skill, zero to three unique
Layer 3 selections independently routed from review risk, and bounded scope.
All assignments share one round. Specialists return current results without
closing Tasks or incrementing rounds, then the primary emits the sole combined
artifact. Every covered Task completion projection references that exact
artifact identity, digest, boundary, round, and current generation. A scoped
material edit invalidates validation and review evidence only for intersecting
scope and transitive Task dependencies; unaffected current evidence remains
reusable. Sharing a Review Boundary never merges Tasks or their Primary
Professional Skills.

## Completion

Completion decisions use the managed projection below. Diagnosis-only and
answer-only work may close when their requested result and proof limits are
fully delivered.

## Core Contract Projection

<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: subagent-model-task-evidence-completion -->
Contract identities:

- Task Contract v2
- visible task-local Evidence Ledger
- completed is terminal for its Task ID

Task Contract v2 fields (exact order):

1. `Task ID`
2. `Status`
3. `Goal`
4. `Owner`
5. `Inputs`
6. `Allowed Read Scope`
7. `Allowed Write Scope`
8. `Non-goals`
9. `Expected Output`
10. `Acceptance`
11. `Verification`
12. `Evidence Requirements`
13. `Parallel Safety`
14. `Workspace Requirement`
15. `Integration Owner`
16. `Review Owner`
17. `Stop Conditions`

New task assignment initial Status:

`in_progress`

visible task-local Evidence Ledger fields (exact order):

1. `Claim`
2. `Owner`
3. `Artifact`
4. `Command`
5. `Result`
6. `Freshness`
7. `Scope`
8. `Proof Limit`
9. `State`

same Task ID transitions (exact):

```text
in_progress -> blocked | partial | completed
blocked -> in_progress | partial | completed
partial -> in_progress | blocked | completed
```

fail-closed outcomes (exact):

```text
validation-failed -> blocked | partial
validation-unavailable -> blocked | partial
high-risk-review-missing -> blocked | partial
blocking-finding-unresolved -> blocked
changed-scope-unreviewed -> blocked | partial
evidence-stale-after-edit -> in_progress | blocked | partial
```

No transition leaves completed for that Task ID.
New work after completion starts `in_progress` under a new Task ID.
<!-- END CHANGEFORGE CORE DOCS PROJECTION: subagent-model-task-evidence-completion -->

## Review Separation

Ordinary implementation work may use the same reviewer instance for re-review.
High-risk work or an explicit separation-of-duty requirement uses a different
reviewer instance. Effective Level determines review depth; the minimum
sufficient Review/Risk Boundary determines frequency. L1-L3 related scope uses
one combined independent final review by default. L4 adds triggered professional
depth, not automatic review rounds. L5 retains independent pre-implementation
and final review. Pre-implementation review targets the named design,
Engineering Brief, Task Plan, or release artifact plus its supporting evidence;
it does not manufacture a changed-file requirement.

Final implementation review targets the latest actual diff and every required
changed file. It reuses fresh, scope-correct, trustworthy-oracle validation
evidence unless a declared reproduction trigger applies. The current Review
Boundary has eight dimensions: Effective Level, one Primary Review Skill,
Required Review Skills, Specialist Obligations, Covered Task IDs, non-empty
Required Changed Scope, Professional Risk Dimensions, and Required Validation /
Evidence Binding for the current generation of every Covered Task ID. A
same-or-stronger current independent review subsumes weaker equivalent
obligations only when all eight dimensions are the same or stronger.

Only material current-task findings affecting Acceptance, correctness or
invariants, regression, security or reliability, or material code health create
a Repair obligation. Adjacent issues, optional cleanup, style preferences,
speculative abstraction, unrelated debt, and future work do not. A fundamental
architecture error, invalid public contract, major security defect, or
fundamentally unmet Acceptance may return `blocked` with Reviewed and Unreviewed
Scope before full review; only `pass` requires all required changed scope to be
reviewed.

After Repair, the Task Agent supplies fresh targeted validation and the Review
Agent performs fresh independent re-review of the original finding, Repair diff,
and affected dependents. Only intersecting, behavior-dependent, and transitively
affected Evidence is invalidated; unaffected fresh Evidence remains current.
Public/shared contracts, schemas, common abstractions, ownership/dependency,
security, transaction/concurrency, or integration impact expands that scope. A
re-review that covers the final current obligation satisfies Final Review
without a duplicate round.
