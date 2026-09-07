---
name: task-dag-planner
description: "`analysis-agent`: plan dependencies between semantic tasks that need ordering, integration or independent work; skip single edits and established plans."
---

# Task DAG Planner

## Role

For `analysis-agent`, turn established engineering decisions into an executable
dependency graph without changing the established behavior, invariants,
ownership, or non-goals.

Inspect decisions, semantic boundaries, blocking edges and workspace safety before scheduling.

## When To Use

- explicit Task DAG request
- multiple tasks with a real dependency parallel benefit integration need or release order

## Do Not Use

- single bounded edit
- existing dependency plan already resolves coordination
- no useful decomposition or dependency question
- agent-count inflation

## Required Inputs

- Accepted source-backed decisions, observable acceptance, candidate scopes,
  shared resources, validation, rollback, and isolation; include review only when justified.

## Professional Decision Rules

- Preserve established acceptance and start with a reversible, verifiable slice that unresolved decisions cannot invalidate.
- Inspect candidate-graph evidence for nodes, edges, blockers, critical path,
  shared-resource collisions, and uncertainty.
- Derive splitting, dependencies, parallel safety, critical path, ownership, and
  remaining tasks from the accepted decisions.
- Do not silently modify acceptance, non-goals, ownership, invariants,
  placement, contract semantics, or rollback.
- Connect tasks by blocking facts; parallelize when it shortens the critical path.
- Require collision-free shared resources for defect-discovery parallelism.
- With shared or unknown workspace, serialize writes.
- Reject parallel writes sharing files, contracts, schemas, migrations, outputs, fixtures, lockfiles, or production resources.
- State each necessary task, accountable owner, scope, and validation; add formal fields only for a real downstream consumer.
- Define each node as one complete semantic change with one primary capability boundary.
- Do not use file, layer, test, or edit-step differences as task boundaries.
- Keep co-effective work together; split materially different professional domains.
- Give each parallel group integration, merge, and conflict-resolution owners
  plus an explicit workspace requirement.
- Add independent review only for an explicit request or a concrete semantic risk that needs independent judgment.
- When review is needed, state its question, scope, and the consumer that depends on its answer.
- Explain the evidence for material dependency and parallelism decisions, with proof limits.

## High-Value Gotchas

- Verification and rollback are obligations, not decorative nodes.
- Shared-contract or workspace writes are not parallel-safe.

## Execution Checklist

1. Confirm decisions, slice, and trigger.
2. Validate graph, workspace, and owners.
3. Project review, integration, validation, rollback, and stops.

## Stop / Escalation Conditions

- Stop when unknown ownership, acceptance, dependency, shared write, verification, or rollback changes safe scheduling.
- Stop on cycles, placeholders, overlapping writes, or a user-owned destructive or production decision.
- Return contradictory decisions and affected scope to their owner before scheduling dependent work.

## Output Contract

- Task DAG preserving the accepted decisions
- necessary tasks and evidence-backed dependency edges
- critical path and safe parallel groups
- integration, conflict-resolution, validation, rollback, and any justified review
- material uncertainty and proof limits
- the next executable change when no DAG is useful

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a quick DAG readiness and closure checklist | Detailed evidence map or executable node contract is required | analysis-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing task dag planner references require dependency, conflict, or output-fragment selection | the task dag planner root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [planning evidence](references/planning-evidence-patterns.md) | evidence-pattern | Closing graph validity, new-hypothesis, parallelization, rollback, or plan-execution consistency | Only task field shape is needed | analysis-agent | evidence-record, proof-limit, residual-risk |
| [task contract](references/task-contract-patterns.md) | benchmark-pattern | Nodes must be executable by a fresh implementer or placeholder tasks need replacement | Existing task contracts already name exact scope, behavior, validation, and residual risk | analysis-agent | option-comparison, selected-approach |
