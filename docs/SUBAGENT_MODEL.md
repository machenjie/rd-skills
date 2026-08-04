# Subagent and Review Model

Subagents are an internal execution method. A request to implement, repair, diagnose, validate, review, or release authorizes the bounded subagents needed to perform it. Ask the user only for a material behavior/scope decision, destructive or production operation, permission elevation, irreversible data change, or an otherwise unknowable requirement.

## Profiles

| Profile | Tools | Owns | Must not do |
| --- | --- | --- | --- |
| `main-control-agent` | dispatch | classification, path, scheduling, progress, review/repair, closure | inspect code, define acceptance/placement, edit, execute, review |
| `analysis-agent` | read, search | current behavior, acceptance, owner, invariants, impact, validation, first slice | edit, dispatch, final review |
| `task-agent` | read, search, edit, execute | one implementation or repair task and targeted validation | widen scope, global reroute, independent final review |
| `review-agent` | read, search, non-modifying execute | implementation diff and changed files, or a bounded pre-implementation artifact; criteria, evidence, findings | edit or repair |

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

## Parallelism

Current supported-host projections may run independent read-only investigation
and review concurrently, but all declare isolated workspaces unsupported and
therefore serialize writes. Parallel writes are only a conditional contract for
a future host-provided isolated workspace with verified non-overlap.
Every parallel group names its Integration Owner, Merge Owner, Conflict
Resolution Owner, and workspace requirement.

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
reviewer instance. Implementation review always targets the latest actual diff
and all changed files. Pre-implementation review instead targets the named
design, Engineering Brief, Task Plan, or release artifact plus its supporting
evidence; it does not manufacture a changed-file requirement.
