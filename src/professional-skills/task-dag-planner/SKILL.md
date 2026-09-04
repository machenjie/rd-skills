---
name: task-dag-planner
description: "`analysis-agent`: create a Task DAG from an accepted source-backed Brief for 2+ semantic tasks with dependency, parallel, integration, or ordering needs; skip single edits, accepted DAGs, and unanalysed requests."
---

# Task DAG Planner

## Role

For `analysis-agent`, turn an accepted Engineering Brief into an executable
dependency graph without changing the Brief's accepted behavior, invariants,
ownership, or non-goals.

Begin by validating the Brief, semantic task boundaries, blocking edges, and
workspace safety. Stop when ownership, dependency, validation, rollback, or safe
scheduling is unknown.

## When To Use

- explicit Task DAG request with accepted Engineering Brief
- accepted Brief has multiple tasks with a dependency parallel benefit integration need or release order

## Do Not Use

- single bounded edit
- task DAG already accepted
- unanalysed change request
- agent-count inflation

## Required Inputs

- Accepted source-backed Brief, observable acceptance, candidate scopes,
  shared resources, validation, rollback, isolation, and review boundaries.

## Professional Decision Rules

- Preserve an accepted First Executable Slice and its acceptance boundary.
- If the Brief does not identify one, recommend the earliest safe, reversible,
  verifiable slice that unresolved analysis cannot invalidate.
- Inspect candidate-graph evidence for nodes, edges, blockers, critical path,
  shared-resource collisions, and uncertainty.
- Record the proof boundary for graph validity.
- Accept or reject each node and edge with an evidence-backed reason before construction.
- Derive splitting, dependencies, parallel safety, critical path, ownership, and
  remaining Task Contracts from the accepted Brief.
- Do not silently modify acceptance, non-goals, ownership, invariants,
  placement, contract semantics, or rollback.
- Return a contradiction to the Brief owner for resolution.
- Create a DAG for multiple real tasks with blocking-fact edges.
- Identify its critical path.
- Parallelize when it shortens the critical path.
- Require collision-free shared resources for defect-discovery parallelism.
- With shared or unknown workspace, serialize writes.
- Reject parallel writes sharing files, contracts, schemas, migrations, outputs, fixtures, lockfiles, or production resources.
- Render a complete Task Contract for every node with one accountable owner.
- Define each node as one complete semantic change with one primary capability boundary.
- Do not use file, layer, test, or edit-step differences as task boundaries.
- Keep co-effective work together; split materially different professional domains.
- Give each parallel group integration, merge, and conflict-resolution owners
  plus an explicit workspace requirement.
- Define minimum sufficient Review Boundaries: combine related work by default
  and require concrete risk for an intermediate boundary.
<!-- rd-semantic-id:v2 finding=unconditional_mechanism_candidate rule=task-dag-planner/review-boundary occurrence=dag-review-boundary -->
- Keep review strategy, scope, independence requirements, and evidence on the
  Review Boundary; task nodes carry only the review obligations they must satisfy.
- Carry graph claims, source evidence, freshness, and proof limits in a visible
  Evidence Ledger.

## High-Value Gotchas

- Verification and rollback are obligations, not decorative nodes.
- Shared-contract or workspace writes are not parallel-safe.

## Execution Checklist

1. Confirm Brief, slice, and trigger.
2. Validate graph, workspace, and owners.
3. Project review, integration, validation, rollback, and stops.

## Stop / Escalation Conditions

- Stop when unknown ownership, acceptance, dependency, shared write, verification, or rollback changes safe scheduling.
- Stop on cycles, placeholders, overlapping writes, or a user-owned destructive or production decision.
- If the Brief is insufficient, a graph conflicts with it, or an accepted
  decision must change, return the contradiction and affected scope to the Brief
  owner before scheduling work.

## Output Contract

- Task DAG preserving the accepted Brief
- status, complete Task Contract nodes, and evidence-backed dependency edges
- critical path and safe parallel groups
- integration, conflict-resolution, validation, rollback, and Review Boundaries
- visible Evidence Ledger with uncertainty and proof limits
- unchanged accepted First Executable Slice when a DAG is unnecessary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a quick DAG readiness and closure checklist | Detailed evidence map or executable node contract is required | analysis-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing task dag planner references require dependency, conflict, or output-fragment selection | the task dag planner root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [planning evidence](references/planning-evidence-patterns.md) | evidence-pattern | Closing graph validity, new-hypothesis, parallelization, rollback, or plan-execution consistency | Only task field shape is needed | analysis-agent | evidence-record, proof-limit, residual-risk |
| [task contract](references/task-contract-patterns.md) | benchmark-pattern | Nodes must be executable by a fresh implementer or placeholder tasks need replacement | Existing task contracts already name exact scope, behavior, validation, and residual risk | analysis-agent | option-comparison, selected-approach |
