# Operating Model

## Source and Built Boundaries

`src/` contains authoring sources: the control model, control prompt, Profile
definitions, registries, Control and Professional Skills, and Layer 3 Skills.
`src/control-model/core-contracts.json` is the authority for roles, Task
Contract v2, Reference Contract v2, Evidence Ledger, completion state, prompt,
Profile, and Control Skill projections. `scripts/build.py` validates those
sources and emits standard artifacts into `dist/`. Installers consume `dist/`
only; build manifests bind the control-model schema and digest.

## Control Flow

```text
request
  -> classify once
  -> Direct Task or Analyzed Work
  -> route one primary Skill per task
  -> bounded task execution
  -> validation of latest edit
  -> independent diff review
  -> repair/re-review when required
  -> explicit closure
```

The main agent schedules mechanically and does not inspect source or rewrite analysis-owned business judgments. Analysis, implementation, and review have separate contexts and tool boundaries.

## Skill Layers

- Control: one Skill for task classification, dispatch, progress, review/repair routing, and closure.
- Professional: complete AI-facing engineering judgment for one work type.
- Foundation/Domain: narrow, high-density rules loaded only for triggered decisions.

Registries declare role support, trigger and anti-trigger signals, required inputs, output contract, escalation signals, and reference index. They contain no private execution-state fields.

Executable tasks and handoffs use the exact schema in the managed Core Contract
Projection below. DAG nodes additionally name `Dependencies`.

## Evidence

Engineering evidence stays observable in handoffs and is never persisted as
private runtime state. Each entry names its evidence-producing agent, freshness,
scope, and proof limit. Implementation completion binds freshness to a current
task-owner claim and current review-agent claims for the latest changed scope.

## Core Contract Projection

<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: operating-model-task-evidence-completion -->
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
<!-- END CHANGEFORGE CORE DOCS PROJECTION: operating-model-task-evidence-completion -->
