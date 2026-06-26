---
name: task-dag-decomposition
description: Decomposes software changes into dependency-aware, reviewable, testable, rollback-aware AI-executable task DAGs with visible sequencing, parallel-safe boundaries, file-scope ownership, and verification outputs.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "77"
changeforge_version: 0.1.0
---

# Mission

Decompose a software change into a directed acyclic graph (DAG) of small, dependency-ordered, independently reviewable, testable, rollback-aware, and agent-executable tasks. The DAG makes dependency chains, source boundaries, repository graph leads, project-memory limits, execution trajectory constraints, validation gates, and parallel-safe file scopes visible before execution so that agents or humans can work in safe increments without hidden ordering, stale context, or false completion claims.

# When To Use

Use this capability when: a change spans multiple files, services, layers, or deployment units; work will be split across multiple agents, developers, or time slots; the change includes a database schema migration, API contract change, breaking dependency update, or infrastructure modification that must be sequenced relative to application code changes; a rollout strategy (canary, feature flag, blue/green) requires coordinating multiple independent deploy steps; or the change is large enough that executing it as a single step would make review, debugging, and rollback impractical.

# Do Not Use When

Do not use this capability for: single-file changes with no cross-cutting dependencies; trivial bug fixes where the fix is already isolated to one function or one test; exploratory prototypes that will be discarded; changes where the entire plan fits on one task (no decomposition benefit).

# Stage Fit

Use during planning after requirement and repository context are sufficient, before implementation or multi-agent handoff. Use again before handoff when the actual changed files, validation commands, repairs, or skipped work must be reconciled against the accepted DAG. Do not let this capability replace `repository-context-map`, `quality-test-gate`, or `release-rollback`; it consumes their evidence and turns it into executable task nodes and dependency edges.

# Non-Negotiable Rules

- **Every task must have an explicit goal, input set, allowed-file scope, dependency list, verification criterion, and done condition.** A task without a done condition cannot be confirmed complete. A task without an allowed-file scope cannot be safely parallelized — another agent may edit the same file concurrently, causing merge conflicts. A task without a verification criterion defers the question "how do we know this works?" to post-merge, which means defects are discovered after integration.
- **Dependencies must be explicit and directional.** "Task 3 depends on Task 1 and Task 2" means: Task 3 cannot begin until Task 1 and Task 2 are both complete and verified. Implicit dependencies (assumed ordering without declaration) are the primary source of integration failures in multi-agent execution. Dependency types: data dependency (Task B reads output produced by Task A), file-scope conflict (both tasks touch the same file), deployment dependency (service B cannot deploy until service A is deployed), test dependency (integration test cannot run until migration and seed data tasks are complete), and migration ordering (schema migration must precede ORM code change in forward direction, but ORM backward-compatibility code must precede schema migration in the rollback direction).
- **Identify parallelizable work explicitly.** Tasks in the same "parallel group" have no inter-dependency and have non-overlapping file scopes. They can be executed concurrently. Tasks NOT in a parallel group must be serialized. The decomposition must call out which tasks can run in parallel, not leave this implicit. Parallel group assignments must be re-verified after any task scope change.
- **Safety and migration tasks must precede their dependents.** Schema migrations precede ORM code that assumes the new schema. Feature flag creation precedes code that reads the flag. Compatibility shims for changed API contracts precede the contract change. Secret or credential rotation precedes the code that reads the new secret. Infrastructure provisioning precedes application code that calls the new infrastructure. Reversing this ordering causes deployment failures or data corruption.
- **Every task that modifies runtime behavior must include a rollback or recovery note.** A rollback note is not "revert the commit." It must specify: what operation in the task is irreversible (schema migration with data transformation, external API call, message queue write), what the rollback sequence is (migration down script, feature flag disable, API gateway rule revert), and who owns the rollback trigger. If a task is irreversible, that must be explicit in the task record so the reviewer can apply additional scrutiny before approval.
- **Task size target: completable in under 2 hours of focused work, reviewable in under 15 minutes.** Tasks that exceed this size are not "one task" — they are multiple tasks with an implicit grouping. A task that edits 15 files, introduces 3 new modules, and changes 2 database tables is four or five tasks. Large tasks reduce review quality, prevent parallel execution, increase rollback blast radius, and are the primary cause of "works on my machine, broken in staging" integration failures.
- **Code-change tasks bind structure and test decisions, and use no placeholders.** A task that adds or changes code records the reuse candidates considered and the placement and visibility decision (schema from `implementation-structure-design`); a task that adds tests records the test level, data, regression target, and deterministic evidence (schema from `quality-test-gate`). Reject placeholder steps — "TODO", "write tests", "handle edge cases", "similar to above" — that name no files, targets, or behavior.
- **Repository graph, project memory, and prior trajectory are selectors, not source truth.** Accept them only after current source, registry, tests, generated artifacts, reports, or owner evidence confirm them; otherwise mark them stale, rejected, or not verified.
- **Every executable task names an independent reviewer and repair route.** The task owner cannot close its own review, and any repair that changes files requires re-review before downstream nodes unblock.

# Industry Benchmarks

Anchor against WBS work packages, trunk-based small batches, progressive delivery, DORA small-batch evidence, dependency-graph formalisms, and LLM agent task design. Keep this body focused on selection, rules, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for task record templates, dependency matrices, graph-memory-trajectory coupling, sequencing decision trees, and anti-pattern examples.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities |
| --- | --- | --- | --- | --- |
| Plan handoff | L1/L2 change has several steps but one owner and low release risk. | Keep a compact task list with validation and stop condition. | Files to inspect/change, validation command, residual risk. | `context-packaging`, `quality-test-gate` |
| Multi-surface DAG | Change crosses frontend/backend/API/data/docs/tests or multiple owners. | Split by independently reviewable artifact, dependency edge, and owner surface. | Nodes, edges, file scopes, critical path, review gates. | `repository-context-map`, `change-impact-analyzer` |
| Safety sequencing | Migration, feature flag, secret, compatibility shim, rollout, or rollback is in scope. | Put safety prerequisites and recovery nodes before dependents. | Forward/rollback ordering, approval gates, verification artifacts. | `release-rollback`, `data-migration-design` |
| Parallelization review | Multiple agents/teams can work concurrently or shared files are likely. | Allow parallel work only after shared mutable resources are ruled out. | Shared-resource scan, non-overlap proof, serialization edges. | `architecture-impact-reviewer`, `implementation-structure-design` |
| Execution recovery | Prior attempt failed, validation is stale, repair changed files, or stop condition is unclear. | Add route-repair, re-review, and validation freshness nodes. | Trajectory summary, failed command, repair route, next validator. | `agent-execution-discipline`, `execution-trajectory-analysis` |

# Selection Rules

Select this capability when **a change has multiple steps that must be sequenced or can be parallelized and the execution order has consequences**.

- Route to `repository-context-map` before planning when ownership, callers, tests, configs, docs, generated artifacts, or source-vs-dist boundaries are not already inspected.
- Route to `repository-graph-analysis` when graph slices can identify source-of-truth, dependents, generated artifacts, or validation candidates; keep graph output bounded.
- Route to `project-memory-governance` when prior failures, fragile files, stale memory, or previous validation affect task ordering or review depth.
- Route to `execution-trajectory-analysis` when validation freshness, repair/re-review, or repeated-failure history affects closure.
- Route to `test-strategy` for deciding which test evidence each task requires.
- Route to `context-packaging` for assembling the file and specification context an agent needs for a specific task.
- Route to `release-rollback` for deployment sequence and rollback triggers.
- Route to `code-review` for per-task review criteria.

# Technical Selection Criteria

Evaluate the DAG against task size, owner surface, dependency type, shared file/resource conflict, safety prerequisite, validation freshness, rollback cost, graph/source freshness, memory reliability, and repair/re-review state. A candidate task is valid only when a different reviewer can verify its artifact without relying on hidden context from adjacent tasks.

# Proactive Professional Triggers

- **Signal:** A task title bundles migration, API contract, authorization, implementation, tests, and deployment. **Hidden risk:** separate risk domains are hidden inside one review unit. **Required professional action:** split by independently reviewable artifact and edge. **Route to:** `task-dag-decomposition`, `quality-test-gate`. **Evidence required:** before/after node split, dependency edge, validation artifact per node, and reviewer for each node.
- **Signal:** Parallel tasks share a router, generated file, migration chain, config file, fixture, queue/topic, database table, feature flag, or public contract. **Hidden risk:** parallel execution creates merge conflict, stale generated output, or inconsistent contract ownership. **Required professional action:** add a serialization edge or split shared-surface ownership before execution. **Route to:** `repository-context-map`, `architecture-impact-reviewer`. **Evidence required:** shared-resource scan, allowed_files comparison, blocked/unblocked parallelism rationale.
- **Signal:** A migration, rollout, secret rotation, or feature flag node lacks forward order, rollback order, owner approval, or old/new coexistence. **Hidden risk:** release cannot roll forward or back without data loss, outage, or secret exposure. **Required professional action:** add safety prerequisite, rollback/recovery node, and validation gate. **Route to:** `release-rollback`, `delivery-release-gate`. **Evidence required:** forward/rollback sequence, validation command, rollback owner, and irreversible-operation flag.
- **Signal:** DAG depends on stale project memory, unrefreshed repository graph, prior validation, or a repair made after review. **Hidden risk:** execution follows stale context or starts downstream work from unreviewed changes. **Required professional action:** require current source confirmation, validation freshness, and repair re-review before unblocking downstream nodes. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** accepted/rejected graph-memory-trajectory judgment, freshness timestamp or direct-source fallback, repair ledger, and re-review result.

# Risk Escalation Rules

Escalate when: a task modifies data that cannot be rolled back without data loss; a task modifies a live-traffic API contract without a backward-compatibility shim preceding it; a task modifies credentials, secrets, or cryptographic keys without rotation sequencing; two tasks have a cyclic dependency; graph or memory evidence conflicts with current source; validation passed before later material edits; a repair changed files without re-review; or the total task count exceeds 30 without a phased release plan.

# Critical Details

- **The most dangerous decomposition failure is a missing migration ordering constraint.** A developer writes the ORM model change (Task A) and the schema migration (Task B) as independent parallel tasks because they are in different files. In the forward direction, both tasks pass in isolation. But in deployment, the ORM code is deployed (reads a column that does not exist yet) — production breaks. In the rollback direction, the schema migration rolls back (drops the column) while ORM code still references it — rollback breaks. The decomposition must represent the ordering constraint explicitly.
- **File-scope reservation prevents merge conflicts in multi-agent execution.** When two agents both edit the same file (e.g., a constants file, an API router, an ORM model) without reservation, the second merge always produces conflicts. The decomposition must ensure that at most one agent "owns" any given file at any point in the execution graph.
- **Verification criteria must be checkable by a different agent than the one that executed the task.** A verification criterion of "looks good" is not a criterion — it is a deferral. Verification must be: executable (run the migration and check the schema diff), observable (the endpoint returns the expected response), or measurable (the test suite passes with 0 failures). This allows a review agent or human reviewer to independently confirm completion.
- **Rollback notes for database migrations must distinguish between schema-safe and data-destructive rollbacks.** Adding a nullable column is safe to roll back (DROP COLUMN, no data to preserve). Dropping a column, transforming existing data, or denormalizing data are irreversible without a prior backup or snapshot. The task record must categorize which rollback type applies and gate the irreversible ones with an explicit approval requirement.
- **Graph-memory-trajectory coupling changes planning depth, not source truth.** A prior memory of a fragile file may add a review or validation node, a graph edge may add a source inspection node, and a stale trajectory may add re-validation, but none of them can prove behavior without current evidence.
- **Changed task to validation mapping prevents false completion.** Every node, edge, safety flag, skipped scope, and parallelism decision maps to a command, review check, owner response, or residual risk.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| All tasks listed as a flat checklist with no dependencies | Execution order ambiguous; migration executed after ORM code; production failure | DAG with explicit dependency edges; topological sort for execution order |
| Two tasks both write to `src/api/routes.ts` with no serialization | Merge conflict on completion of second task; changes lost | One task owns the file; other task depends on it; or tasks are merged into one |
| Verification: "developer confirms it looks right" | Unverifiable by review agent; quality gate bypassed | Concrete check: "npm test passes with 0 failures" or "schema shows column X" |
| Rollback for migration task: "just revert the commit" | Data already written to new column; DOWN migration destroys data | Explicit DOWN migration; data backup step preceding it if data-destructive |
| Feature flag task not created before code that reads the flag | Flag read fails on deploy; application throws on startup | Feature flag creation task (T-001) as dependency of all tasks reading the flag |
| 25-file refactor in one task | Unreviable; unrollbackable; blocks all parallel work | Decompose into 5-file tasks by concern; identify parallel groups |

# Failure Modes

- Migration deployed after ORM code: column does not exist; application crashes on first query.
- Parallel tasks write to same file: second agent's change overwrites first; silent data loss.
- Feature flag not pre-created: code reads undefined flag; default behavior incorrect; silent rollout failure.
- Rollback triggered on data-destructive migration without backup: permanent data loss.
- Cyclic task dependency: Task A depends on B, B depends on A; neither can start; deadlock.
- Task scope too large: 15-file task reviewed in 2 minutes; defect missed in review; escapes to production.
- Verification deferred to post-merge integration test: defect discovered after merge; rollback required.
- Project memory says a dependent file is irrelevant, but current graph/source inspection would have shown it changed.
- Repair updates a task node after review and downstream work starts without re-review.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 selection, rules, output, and gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete DAG. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when task templates, dependency classification, graph-memory-trajectory coupling, migration/API/feature-flag sequencing, parallelism review, or validation mapping needs more depth. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear.

# Output Contract

Return a task DAG with:

- `mode_selected` (plan handoff, multi-surface DAG, safety sequencing, parallelization review, or execution recovery)
- `boundaries_inspected` (repository source, callers/callees, tests, configs, docs, registry/generated artifacts, graph slice, memory signals, prior trajectory, and skipped boundaries with reason)
- `source_evidence` (current facts that support task nodes and edges, with not-verified markers for missing evidence)
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, or not verified claims and their effect on DAG scope)
- `tasks` (per task: id, title, goal, owner_surface, inputs, files_to_inspect, allowed_files, reuse_and_placement, dependencies, parallel_group, validation_command, expected_output, done_condition, completion_evidence, rollback_notes, review_gate, repair_route, safety_flag)
- `dependency_graph` (edges: task_id -> task_id with dependency type and reason)
- `parallel_groups` (named groups with no inter-dependency and non-overlapping file/resource scopes)
- `critical_path` (minimum serialized execution sequence and estimated duration)
- `safety_flags` (irreversible operations, approval requirements, rollback owner)
- `migration_ordering` and `phased_release_plan` when applicable
- `cycle_check` (acyclic confirmation or cycles to resolve)
- `changed_task_to_validation_map` (each node, edge, safety flag, parallelism decision, skipped scope, and repair route mapped to validator, review, owner response, or residual risk)
- `plan_execution_consistency` (accepted DAG vs actual changed files, validation freshness, skipped work, unplanned changes, and residual risk before handoff)
- `evidence_limits` and `next_gate`

# Evidence Contract

Close a task DAG only when these answers are concrete:

- **Basis:** request, requirement facts, repository evidence, dependency facts, and risk class that justify each task and edge.
- **Current evidence inspected:** source files, registry/config/docs, tests, generated artifacts, graph slice, memory signals, and execution trajectory accepted or rejected.
- **Placement and parallelism rationale:** why each node is a single reviewable unit, why new structure is placed there, and why parallel groups cannot collide.
- **Validation and repair:** command/check/review evidence for each task, freshness after edits, what evidence proves and does not prove, rollback path, repair owner, and re-review rule.
- **Handoff and residual risk:** changed-task-to-validation map, evidence limits, unresolved owner decisions, next gate, and closure boundary.

# Benchmark Coverage

This capability covers work-package decomposition, DAG dependency modeling, critical path, merge-conflict prevention, migration/API/feature-flag sequencing, rollback-aware task design, agent-executable task contracts, graph/memory/trajectory freshness, and plan-execution consistency. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for deeper templates and matrices.

# Routing Coverage

Routes from `task-dag-planner`, `change-forge-router`, `change-impact-analyzer`, and execution/review gates should arrive here when task ordering, parallelism, validation placement, or rollback sequencing is the core problem. Route away when the primary need is requirement clarification, context packaging for one node, detailed test strategy, release rollout mechanics, or code review of completed artifacts.

# Quality Gate

The task DAG is complete only when:

1. Every task has goal, inputs, allowed_files, dependencies, verification, done_condition, and rollback_notes.
2. No two tasks in the same parallel group share a file in their allowed_files scope.
3. All migration ordering constraints are explicit in both forward and rollback directions.
4. Safety tasks (migrations, flag creation, shims, secrets rotation) precede all dependents.
5. Every in-progress state has at least one rollback or recovery path.
6. All verification criteria are independently executable or observable (not "looks good").
7. All tasks are ≤ 2-hour scope (single concern, bounded file set).
8. The DAG is verified acyclic.
9. The critical path is identified.
10. A phased release plan is present for multi-deployment changes.
11. Code-change tasks record reuse candidates and a placement decision; test tasks record level, data, regression target, and evidence.
12. No task uses a placeholder (TODO, "write tests", "handle edge cases", "similar to above") in place of named files, targets, or behavior.
13. Graph, memory, and trajectory claims are accepted, rejected, stale, or not verified against current evidence.
14. Every node, edge, safety flag, parallelism decision, skipped scope, and repair route maps to validation, review, owner response, or residual risk.
15. Plan-execution consistency is checked before final handoff, including validation freshness after final material edits.

# Used By

- task-dag-planner

# Handoff

Hand off to `context-packaging` for assembling task execution context; `test-strategy` for per-task test requirements; `release-rollback` for deployment sequence and rollback design; `code-review` for per-task review criteria; `agent-execution-discipline` when trajectory, evidence, repair/re-review, or closure discipline is incomplete; and `plan-execution-consistency` before final handoff.

# Completion Criteria

The capability is complete when the dependency graph is explicit, source evidence is fresh enough for the plan, graph/memory/trajectory claims are scoped, parallelizable work has non-conflicting files/resources, safety tasks precede dependents, every task has independent verification and rollback or recovery, and the downstream path can execute without guessing task order, validation evidence, or closure boundaries.
