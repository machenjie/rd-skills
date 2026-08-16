---
name: task-dag-planner
description: "Use `analysis-agent` to create a Task DAG from an accepted source-backed Brief when 2+ tasks have dependencies, parallel value, integration, or release order. Skip single edits, accepted DAGs, and unanalysed requests."
---

# Task DAG Planner

## Role

Support `analysis-agent` in projecting Task Contract v2 nodes from the current
Engineering Brief. The Brief retains sole operational analysis authority.

Begin by validating the Brief, semantic Task boundaries, blocking edges, and workspace
safety. Stop when ownership, dependency, validation, rollback, or safe
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

- Preserve its First Executable Slice verbatim.
- Never select the First Executable Slice.
- Never replace the First Executable Slice.
- Never reinterpret the First Executable Slice.
- Inspect `task-dag-decomposition` candidate-graph evidence for nodes, edges, blockers, critical path, collisions, uncertainty, and proof limits.
- Accept or reject each node and edge with an evidence-backed reason before construction.
- Project splitting, dependencies, parallel safety, critical path, ownership, and remaining Task Contracts only.
- Never modify Acceptance, Non-goals, Owner, Invariants, Placement, contract
  semantics, or Rollback. A Task DAG and its nodes are derived artifacts, not a parallel analysis authority.
- Create a DAG for multiple real tasks with blocking-fact edges.
- Identify its critical path.
- Parallelize only when it shortens that path or adds independent defect discovery.
- With shared or unknown workspace, serialize writes.
- Reject parallel writes sharing files, contracts, schemas, migrations, outputs, fixtures, lockfiles, or production resources.
- Render complete Task Contract v2 nodes with one Owner.
- Define each node as one complete semantic change and Primary Professional Skill.
- Keep co-effective work together; split materially different professional domains.
- File, layer, test, and edit-step differences do not define Tasks.
- Give each parallel group Integration, Merge, Conflict Resolution owners and a workspace requirement.
- Define minimum sufficient Review Boundaries: combine related work by default and require concrete risk for an intermediate boundary.
- Preserve each Task's Primary Skill, implementation Layer 3, Review Skills, Specialist obligations, and risk dimensions.
- Keep strategy, frequency, assignments, round ID, and primary-close ordering on the global Review Boundary; Task nodes carry only requirements.
- Give the boundary one primary and zero or more specialist review-agent assignments, each with an ID, role, one registered Review Skill, zero to three independently risk-routed Layer 3 Skills, and bounded scope.
- Share one Review Round ID: specialists neither close Tasks nor add rounds; the primary waits for current required results and emits the sole artifact and Task projections.
- Carry graph claims and proof limits in the visible task-local Evidence Ledger.

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
- If the Brief is insufficient, a projection conflicts with it, or a protected
  decision must change, return `blocked` through Main to analysis for an updated
  Brief and redispatch of affected tasks.

## Output Contract

- derived Task DAG Contract v2 preserving the Brief
- Status and complete task nodes
- parallel-group, Integration Owner, and Review Owner boundaries
- one Primary Professional Skill per Task and sufficient Review Boundaries
- visible task-local Evidence Ledger
- unchanged Brief First Executable Slice when a DAG is unnecessary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a quick DAG readiness and closure checklist | Detailed evidence map or executable node contract is required | analysis-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing task dag planner references require dependency, conflict, or output-fragment selection | the task dag planner root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [planning evidence](references/planning-evidence-patterns.md) | evidence-pattern | Closing graph validity, new-hypothesis, parallelization, rollback, or plan-execution consistency | Only task field shape is needed | analysis-agent | evidence-record, proof-limit, residual-risk |
| [task contract](references/task-contract-patterns.md) | benchmark-pattern | Nodes must be executable by a fresh agent or placeholder tasks need replacement | L1/L2 handoff already has exact files, command, and residual risk | analysis-agent | option-comparison, selected-approach |
