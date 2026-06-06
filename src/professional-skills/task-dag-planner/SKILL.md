---
name: task-dag-planner
description: Breaks a product or code change into small dependency-aware, reviewable, testable, rollback-aware tasks with explicit ordering, parallelization opportunities, validation points, and handoff boundaries.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Task DAG Planner

## Mission
Decompose a complex product or code change into a directed acyclic graph (DAG) of small, dependency-ordered, independently reviewable, and rollback-aware tasks — so that implementation can proceed in safe increments, risky changes are never hidden inside broad implementation buckets, verification is built into the graph rather than bolted on at the end, and every rollback path has an explicit owner and procedure.

## When To Use
- After intake and impact analysis, when a change needs sequencing, parallel work coordination, or multi-team dependency management.
- When a change involves a database migration, API contract change, and application code change that must be deployed in a specific order.
- When the change spans multiple bounded contexts, services, or teams with coordination dependencies.
- When feature flags, progressive rollout, or EMC (Expand/Migrate/Contract) phases need to be sequenced explicitly.
- When a cross-cutting refactoring needs to be decomposed into safe, verifiable slices.
- When the rollback path for a complex change needs to be designed and validated as part of the plan.
- When a product change needs to be decomposed into reviewable increments that each produce a shippable artifact.

## Do Not Use When
- A single obvious edit with no dependency, test, release, or coordination risk — create the task directly without a DAG.
- The change is a documentation-only update with no implementation dependencies.

## Non-Negotiable Rules
- **Tasks must be small enough to review in a single pass**: a task that requires reviewing 5 modules simultaneously is not a task, it is a phase — break it down further.
- **All dependencies between tasks must be explicit**: implicit sequencing assumptions cause parallel work collisions; if Task B requires Task A's output, that dependency must be in the graph.
- **Verification tasks are first-class nodes in the graph**: test, validate, and verify tasks are not afterthoughts — they are blocking gates that prevent downstream work from starting until evidence is produced.
- **Rollback tasks are first-class nodes**: for every irreversible or high-risk task (migration, deployment, external notification), there must be a corresponding rollback task in the graph with a tested rollback procedure.
- **Do not hide risky changes in broad implementation tasks**: a task named "implement backend changes" that includes a schema migration, an authorization change, and a breaking API change is three tasks disguised as one.
- **Migration tasks must precede code tasks that depend on the migrated state**: deploying code that expects a new schema before the migration runs causes immediate production failure.
- **Feature flag tasks must precede feature implementation tasks**: a feature behind a flag requires the flag to be registered and defaulted off before any implementation ships.
- **Parallelism must be explicit**: tasks that can safely run concurrently must be identified — undetected sequential bottlenecks delay delivery; undetected parallel conflicts corrupt work.

## Industry Benchmarks
- **Work Breakdown Structure (WBS — PMI PMBOK 7th Edition)**: Hierarchical decomposition of deliverables into work packages. Each work package is assignable, estimable, and independently verifiable.
- **Trunk-Based Development (Forsgren, Humble, Kim — Accelerate)**: Small, frequent commits to trunk; feature flags protect incomplete work; no long-lived feature branches. Tasks in the DAG should map to trunk-based commits.
- **Dependency-First Task Ordering (Critical Path Method)**: Identify the critical path — the longest chain of dependent tasks. Compress non-critical tasks into the critical path by parallelizing where possible.
- **Expand/Migrate/Contract (Database Migration Pattern)**: Phase 1 Expand: add new schema element, code supports both old and new; Phase 2 Migrate: move data or consumers to new element; Phase 3 Contract: remove old element. Each phase is a separate deployable task.
- **Story Slicing (Richard Lawrence — Elephant Carpaccio)**: Slice user stories into thin, independently demonstrable vertical slices — each produces working software, not just a layer of the stack.
- **Kanban Flow Efficiency**: Work that spends more time waiting than being worked on has low flow efficiency. Tasks blocked by unmet dependencies reduce flow — make dependencies explicit to unblock.
- **Rollback as a Designed Artifact (SRE Release Engineering)**: Rollback is a product of engineering discipline, not an emergency improvisation. Every high-risk task has a pre-built, tested rollback procedure that can be executed in under 5 minutes.

### Task Granularity Guidelines

| Task Size Signal | Assessment | Action Required |
|---|---|---|
| Task takes > 1 day to implement | Probably too large | Decompose into smaller slices; look for vertical cuts |
| Task produces no independently reviewable artifact | Not a task — it's a phase | Split until each sub-task produces its own reviewable evidence |
| Task has > 3 hard dependencies | Central bottleneck | Look for ways to reduce dependencies or parallelize precursors |
| Task involves > 2 bounded contexts | Cross-cutting | Separate per context; add coordination tasks |
| Task combines migration + code + deployment | Three tasks as one | Separate: migration task → code task → deployment task |
| Task has no verification step | Incomplete | Add a verification task after; define acceptance criteria |

## Technical Selection Criteria
Evaluate the task decomposition against:
- **Dependency completeness**: Are all blocking relationships between tasks expressed? Is the DAG acyclic (no circular dependencies)?
- **Critical path identification**: Which task sequence determines the earliest completion date? What is the longest chain?
- **Parallelism opportunities**: Which tasks have no shared dependencies and can run simultaneously?
- **Migration sequencing**: Is schema migration (Expand) before application deployment, not after?
- **Feature flag readiness**: Is the flag created and defaulted to off before any feature code ships?
- **Contract compatibility window**: During a rolling deployment, do old and new application versions coexist safely?
- **Verification task placement**: Is there a verification gate after each high-risk task (migration, deployment, integration point)?
- **Rollback task placement**: For each irreversible task, is the corresponding rollback task defined and linked?
- **Owner assignment**: Does each task have an identified owner surface (backend, frontend, data, infrastructure, release)?
- **Residual risk per task**: For each task, is the rollback or undo cost identified and acceptable?

### Decision Tree: Task Sequencing for Data + Code + Deploy

```
Does the change include a database migration?
├── Yes → Task 1: Expand migration (backward-compatible with current code)
│         Task 2: Deploy new code (uses both old and new schema during rollout)
│         Task 3: Contract migration (removes old schema after all instances updated)
Does the change include a breaking API change?
├── Yes → Task 1: Deploy new API version alongside old
│         Task 2: Migrate consumers to new version
│         Task 3: Deprecate and remove old version
Does the change include a feature flag?
├── Yes → Task 1: Register flag (default off)
│         Task 2: Implement feature behind flag
│         Task 3: Staged rollout (1% → 10% → 100%)
│         Task 4: Cleanup (remove flag after full rollout)
Does the change require multi-team coordination?
├── Yes → Add coordination tasks as explicit blocking nodes
No complex sequencing?
└── Decompose into: implement → test → review → deploy → verify
```

## Risk Escalation Rules
- Escalate when a migration task is irreversible and the rollback task would require manual data correction — an untested rollback at that task is a P1 incident waiting to happen.
- Escalate when concurrent tasks would produce write conflicts on a shared resource (shared table, shared configuration, shared API contract).
- Escalate when a cross-service contract change requires coordinated deployment of two or more services simultaneously — the sequencing must be validated before execution starts.
- Escalate when a task requires directly correcting production data — data correction tasks require separate review, backup, and approval.
- Escalate when a task cutover from one external dependency to another (payment processor migration, DNS migration) cannot be rolled back within the deployment window.
- Escalate when no single owner can be identified for a task — unclear ownership means unclear accountability when the task produces an incident.
- Escalate when the critical path exceeds the available release window — the plan needs compression, parallelization, or scope reduction.

## Critical Details
- **DAG validation rule**: run a topological sort on the task graph before execution begins. If the sort fails (cycle detected), the graph has a circular dependency — resolve before implementation starts.
- **Task granularity is not about size, it is about reviewability**: a task is correctly sized when a reviewer can confirm it is complete, correct, and safe without needing context from adjacent tasks.
- **The DAG reveals hidden risk**: a task that has 6 incoming dependencies is the riskiest task in the plan — all six must complete successfully before it can start, and any delay in any of them delays the entire plan.
- **Parallelism requires isolation**: two tasks can run in parallel only if they do not share mutable state, shared database tables with locking risk, or shared API contracts that both modify simultaneously.
- **Rollback is time-bound**: a rollback task that cannot be executed in under 5 minutes for critical-path changes is a rollback plan in name only. If rollback takes 45 minutes, the change requires a maintenance window.
- **Verification tasks produce artifacts**: a verification task is not "check that it works." It is "run integration test suite and attach results" or "perform EXPLAIN ANALYZE on migration and confirm < 100ms on test data." The artifact is the evidence.
- **Feature flag lifecycle as DAG nodes**: create, rollout, and cleanup are three separate tasks. The cleanup task (flag removal) is frequently omitted — it must be a first-class node with an explicit deadline.

### Anti-Examples

| Planning Pattern | Problem | Corrected Approach |
|---|---|---|
| Task: "Implement backend changes" (includes migration + auth change + API change) | Three distinct risks in one unreviewed task | Three tasks: migration (with rollback task), auth change (with IDOR test task), API change (with consumer notification task) |
| Migration task has no rollback task | Rollback improvised under incident pressure | Rollback task: "Execute rollback migration; verify old code functions with restored schema" |
| Task sequence: code → migration → deploy | New code runs on old schema; crashes immediately | Correct sequence: migration → code → deploy |
| All tasks sequential, no parallelism | Delivery time = sum of all tasks | Frontend and backend tasks with no shared state run in parallel |
| Feature flag cleanup task not in DAG | Flag never removed; becomes permanent complexity | Flag cleanup task with deadline added to DAG before work begins |

## Failure Modes
- **Large tasks hide defects**: a 300-line PR combining migration + feature + auth change gets approved because the reviewer cannot evaluate all three simultaneously.
- **Missing dependencies block execution**: Task B starts before Task A completes — the shared database table has old schema; Task B's writes fail.
- **No rollback task creates an unrecoverable incident**: a migration is deployed; it causes a production outage; there is no tested rollback procedure; the incident extends to hours.
- **No verification task creates false completion**: all implementation tasks are marked done; the feature is deployed; a critical integration test that would have caught a regression was never run.
- **Circular dependency discovered during execution**: Tasks A and B each depend on the other's output — neither can start; the plan is deadlocked.
- **Parallel tasks create a write conflict**: two teams modify the same database migration file simultaneously — the merge conflict is resolved incorrectly; both migrations run, one corrupting the other's schema.
- **Critical path not identified**: the team parallelizes low-risk frontend tasks while the high-risk migration task (the bottleneck) is assigned to a single engineer with no backup — delivery is delayed by the unidentified critical path.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a task DAG with:
- **Task nodes**: Each with ID, title, objective, owner surface, dependencies (IDs), parallelism flag, and completion condition.
- **Dependency graph**: Explicit directed edges showing which tasks must complete before which.
- **Critical path**: The longest sequence of dependent tasks determining minimum delivery time.
- **Verification nodes**: Gate tasks that block downstream work until evidence is produced.
- **Rollback nodes**: Rollback tasks linked to each irreversible or high-risk task, with tested procedure.
- **Migration sequence**: Expand → code → contract phases in correct dependency order.
- **Feature flag lifecycle**: Create → implement → rollout → cleanup nodes in sequence.
- **Parallelism map**: Sets of tasks that can safely execute concurrently.
- **Risk per task**: Rollback cost and reversibility for each high-risk task.
- **Residual risk summary**: Accepted risks with justification and mitigating controls.

## Evidence Contract
Close a task DAG only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the change request and dependency facts each task and edge rests on.
- **Files and boundaries inspected**: the surfaces, owners, and shared artifacts each task touches, and the tasks that therefore cannot run concurrently because they would collide on the same file or resource.
- **Placement rationale**: why each node is a single reviewable patch unit with a named input, output, owner, and dependency edge, and why the parallelism map is safe.
- **Validation commands**: the verification node attached to each task — the literal command or check that must pass before downstream work unblocks — and the rollback procedure for each irreversible task.
- **Residual risk**: the sequencing or rollback assumption that remains unproven, with the named owner.

## Quality Gate
1. All task dependencies form a valid DAG (no circular dependencies; topological sort succeeds).
2. No task combines more than one distinct risk domain (migration, authorization change, API change) into a single unreviewed unit.
3. Every high-risk or irreversible task has a corresponding rollback task with a tested procedure.
4. Every integration point, migration, and deployment has a verification gate task.
5. Migration tasks are sequenced before application code tasks that depend on the migrated state.
6. Feature flag tasks include creation, rollout, and cleanup nodes.
7. All parallelizable tasks are identified; no unnecessary sequential bottlenecks remain.
8. Every task has an identified owner surface.
9. The critical path is identified and its delivery time is within the release window.
10. All tasks produce independently reviewable artifacts that can confirm completion without requiring cross-task context.

## Handoff
- **backend-change-builder** — receives backend task nodes with dependencies, completion criteria, and rollback notes.
- **data-api-contract-changer** — receives migration sequencing task nodes with EMC phases.
- **delivery-release-gate** — receives the deployment and rollback task nodes with sequencing and verification gates.
- **quality-test-gate** — receives verification task nodes with required test evidence per task.
- **architecture-impact-reviewer** — receives the DAG for cross-context coordination task review.
- **domain-impact-modeler** — if domain boundary coordination tasks need inter-team dependency sequencing.

## Completion Criteria
The task DAG is complete when it forms a valid acyclic graph, every high-risk task has a tested rollback task, every integration point has a verification gate, migrations are sequenced before dependent code, feature flag lifecycle is fully represented, all parallelism opportunities are identified, the critical path is calculated and fits the delivery window, and every task has an identified owner surface and independently reviewable completion artifact.
