---
name: task-dag-planner
description: "Use `analysis-agent` to create a Task DAG from an accepted source-backed Brief when 2+ tasks have dependencies, parallel value, integration, or release order. Skip single edits, accepted DAGs, and unanalysed requests."
---

# Task DAG Planner

## Role

Support `analysis-agent` in selecting the First Executable Slice and emitting
the sole final authoritative Task DAG and Task Contract v2 for genuine multi-task work.

## When To Use

- explicit Task DAG request with accepted Engineering Brief
- accepted Brief has multiple tasks with a dependency parallel benefit integration need or release order

## Do Not Use

- single bounded edit
- task DAG already accepted
- unanalysed change request
- To increase agent count or delay an already safe first slice.

## Required Inputs

- Accepted source-backed Engineering Brief, owner boundaries, and observable acceptance.
- Candidate read/write scopes, shared contracts and resources, validation entry points, rollback needs, and host workspace isolation capability.
- Resource and review boundaries for ordinary, combined, and specialized review.

## Professional Decision Rules

- Expose the First Executable Slice once remaining analysis cannot invalidate it.
- Inspect `task-dag-decomposition` candidate-graph evidence for proposed nodes, edges, blockers, critical path, collisions, uncertainty, and proof limits.
- Accept or reject each proposed node and edge with an evidence-backed reason before constructing the graph.
- Select the First Executable Slice independently under this Skill's ownership.
- Only this Skill emits the final authoritative Task DAG and Task Contract v2.
- Create a DAG only for two or more real tasks whose every edge expresses a blocking fact.
- Identify the critical path and parallelize only when it shortens that path or adds independent defect discovery.
- Mark workspace requirement and parallel safety. With shared or unknown workspace, serialize every write task.
- Reject parallel writes that share files, contracts, schemas, migrations, generated outputs, fixtures, lockfiles, or production resources.
- Render every node with the authoritative Task Contract v2 and one accountable Owner.
- Give every parallel group an Integration Owner, Merge Owner, Conflict Resolution Owner, and workspace requirement.
- Carry graph claims and proof limits in the visible task-local Evidence Ledger.

## High-Value Gotchas

- A broad “implement backend” node hides ownership, migration, authorization, and rollback risks.
- Verification and rollback are obligations on risky tasks, not decorative nodes.
- Independent work is not parallel-safe when it mutates a shared contract or workspace.
- A cycle or placeholder means the work is not executable.

## Execution Checklist

1. Identify the First Executable Slice.
2. Decide whether a DAG is actually required.
3. Split only by independent owner, risk, dependency, review, or validation boundary.
4. Check every dependency and shared mutable resource.
5. Mark critical path, parallel-safe tasks, and workspace requirement.
6. Define per-task and combined review contracts, integration, validation, rollback, and stop boundaries.

## Stop / Escalation Conditions

- Stop for an unknown owner, acceptance, dependency, shared write, verification entry, or rollback boundary that changes safe scheduling.
- Stop on cycles, placeholders, overlapping writes, or a user-owned destructive or production decision.

## Output Contract

- sole authoritative Markdown Task DAG Contract v2
- Status and complete task nodes
- parallel-group, Integration Owner, and Review Owner boundaries
- visible task-local Evidence Ledger
- single Task Capsule when a DAG is unnecessary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a quick DAG readiness and closure checklist | Detailed evidence map or executable node contract is required | analysis-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing task dag planner references require dependency, conflict, or output-fragment selection | the task dag planner root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [planning evidence](references/planning-evidence-patterns.md) | evidence-pattern | Closing graph validity, new-hypothesis, parallelization, rollback, or plan-execution consistency | Only task field shape is needed | analysis-agent | evidence-record, proof-limit, residual-risk |
| [task contract](references/task-contract-patterns.md) | benchmark-pattern | Nodes must be executable by a fresh agent or placeholder tasks need replacement | L1/L2 handoff already has exact files, command, and residual risk | analysis-agent | option-comparison, selected-approach |
