---
name: task-dag-decomposition
description: Decomposes work into small dependency-aware, reviewable, testable, rollback-aware AI-executable tasks.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "77"
changeforge_version: 0.1.0
---

# Mission

**Decompose a software change into a directed acyclic graph (DAG) of small, dependency-ordered, independently reviewable, testable, and rollback-aware tasks** — making dependency chains visible before execution so that parallel-safe work is identified, merge conflicts are prevented through file-scope reservation, safety-critical tasks (migrations, compatibility shims, feature flags, secrets rotation) are scheduled before their dependents, and each task produces a verifiable output that an AI agent or human developer can review and confirm before the next task begins.

# When To Use

Use this capability when: a change spans multiple files, services, layers, or deployment units; work will be split across multiple agents, developers, or time slots; the change includes a database schema migration, API contract change, breaking dependency update, or infrastructure modification that must be sequenced relative to application code changes; a rollout strategy (canary, feature flag, blue/green) requires coordinating multiple independent deploy steps; or the change is large enough that executing it as a single step would make review, debugging, and rollback impractical.

# Do Not Use When

Do not use this capability for: single-file changes with no cross-cutting dependencies; trivial bug fixes where the fix is already isolated to one function or one test; exploratory prototypes that will be discarded; changes where the entire plan fits on one task (no decomposition benefit).

# Non-Negotiable Rules

- **Every task must have an explicit goal, input set, allowed-file scope, dependency list, verification criterion, and done condition.** A task without a done condition cannot be confirmed complete. A task without an allowed-file scope cannot be safely parallelized — another agent may edit the same file concurrently, causing merge conflicts. A task without a verification criterion defers the question "how do we know this works?" to post-merge, which means defects are discovered after integration.
- **Dependencies must be explicit and directional.** "Task 3 depends on Task 1 and Task 2" means: Task 3 cannot begin until Task 1 and Task 2 are both complete and verified. Implicit dependencies (assumed ordering without declaration) are the primary source of integration failures in multi-agent execution. Dependency types: data dependency (Task B reads output produced by Task A), file-scope conflict (both tasks touch the same file), deployment dependency (service B cannot deploy until service A is deployed), test dependency (integration test cannot run until migration and seed data tasks are complete), and migration ordering (schema migration must precede ORM code change in forward direction, but ORM backward-compatibility code must precede schema migration in the rollback direction).
- **Identify parallelizable work explicitly.** Tasks in the same "parallel group" have no inter-dependency and have non-overlapping file scopes. They can be executed concurrently. Tasks NOT in a parallel group must be serialized. The decomposition must call out which tasks can run in parallel, not leave this implicit. Parallel group assignments must be re-verified after any task scope change.
- **Safety and migration tasks must precede their dependents.** Schema migrations precede ORM code that assumes the new schema. Feature flag creation precedes code that reads the flag. Compatibility shims for changed API contracts precede the contract change. Secret or credential rotation precedes the code that reads the new secret. Infrastructure provisioning precedes application code that calls the new infrastructure. Reversing this ordering causes deployment failures or data corruption.
- **Every task that modifies runtime behavior must include a rollback or recovery note.** A rollback note is not "revert the commit." It must specify: what operation in the task is irreversible (schema migration with data transformation, external API call, message queue write), what the rollback sequence is (migration down script, feature flag disable, API gateway rule revert), and who owns the rollback trigger. If a task is irreversible, that must be explicit in the task record so the reviewer can apply additional scrutiny before approval.
- **Task size target: completable in under 2 hours of focused work, reviewable in under 15 minutes.** Tasks that exceed this size are not "one task" — they are multiple tasks with an implicit grouping. A task that edits 15 files, introduces 3 new modules, and changes 2 database tables is four or five tasks. Large tasks reduce review quality, prevent parallel execution, increase rollback blast radius, and are the primary cause of "works on my machine, broken in staging" integration failures.

# Industry Benchmarks

Anchor against: **PMI PMBOK — Work Breakdown Structure (WBS)** — hierarchical decomposition of project scope into smaller components; work package definition; 100% rule (WBS must represent the total scope). **Trunk-Based Development (Google/Thoughtworks)** — short-lived branches; incremental changes; feature flags to decouple deploy from release; branch-by-abstraction for large refactors. **Progressive Delivery / Feature Flags (LaunchDarkly, Unleash)** — decouple code deployment from feature activation; enable rollback without code revert; canary traffic routing. **Gitflow / GitHub Flow / Trunk branching strategies** — merge conflict prevention through small branches; task scope limiting to one concern. **DORA Research** — small batch size is one of the four key metrics correlated with high delivery performance; large batch sizes correlate with high change failure rate and low deployment frequency. **OpenAI Evals / LLM agent task design** — task clarity, bounded context, verifiable output, and tool restriction are key to reliable AI agent execution. **Dependency Graph (DAG) formalisms** — topological sort for execution order; cycle detection (cyclic dependencies cannot be executed); critical path analysis for identifying the serialized minimum duration path.

### Task Record Template

```yaml
task_id: "T-012"
title: "Add user_tier column to accounts table"
goal: >
  Add nullable user_tier VARCHAR(20) column to the accounts table via a
  backward-compatible migration. Column must be addable without downtime
  (no NOT NULL without DEFAULT on live table).
inputs:
  - accounts table schema (current)
  - data model spec (user_tier values: 'free', 'pro', 'enterprise')
allowed_files:
  - db/migrations/20240801_add_user_tier_to_accounts.sql
  - db/schema.rb  # or equivalent ORM schema file
dependencies:
  - T-010  # data model spec must be finalized before migration is written
parallel_group: null  # cannot parallelize with T-013 (ORM model update)
verification:
  - Migration runs cleanly on a copy of the production schema (no errors)
  - Migration is backward-compatible: existing queries that do not reference user_tier still pass
  - Column is nullable with no NOT NULL constraint in this migration step
  - `rails db:rollback` (or `migrate down`) succeeds cleanly
done_condition: >
  Migration file created, reviewed, run against staging schema snapshot,
  and rollback tested. Schema dump shows user_tier column as nullable VARCHAR(20).
rollback_notes: >
  Rollback: run the down migration to DROP COLUMN. The column has no NOT NULL
  constraint and no foreign key, so dropping it is safe. If this migration was
  deployed in production and user_tier values were written, the down migration
  must be confirmed with data team before execution (data loss check).
review_evidence:
  - Migration reviewed for: backward compatibility, NULL safety, index plan
  - Staging schema diff attached
safety_flag: false  # no irreversible data transformation in this migration step
```

### Dependency Classification Matrix

| Dependency Type | Serialization Requirement | Common Failure if Ignored |
| --- | --- | --- |
| Data dependency | Task B after Task A (A produces input B needs) | B fails at runtime because expected output does not exist |
| File-scope conflict | Cannot parallelize; one task completes before other starts | Merge conflict; one task overwrites the other's changes |
| Deployment dependency | Service B deploys after Service A (B calls A's new endpoint) | Service B startup fails: endpoint not found |
| Test dependency | Integration tests run after migration + seed data tasks | Tests fail: table/column not yet present in test DB |
| Migration ordering (forward) | Schema migration before ORM code using new schema | ORM query fails: column does not exist |
| Migration ordering (rollback) | ORM backward-compat code before schema migration reversal | Rollback breaks live traffic reading dropped column |

# Selection Rules

Select this capability when **a change has multiple steps that must be sequenced or can be parallelized and the execution order has consequences**. Route to `test-strategy` for deciding which tests each task requires. Route to `context-packaging` for assembling the file and specification context an agent needs for a specific task. Route to `release-rollback` for designing the deployment sequence and rollback triggers at the release level. Route to `code-review` for the review criteria applied to individual task outputs.

# Risk Escalation Rules

Escalate when: a task modifies data that cannot be rolled back without data loss (must flag as irreversible and require explicit stakeholder sign-off before execution); a task modifies a live-traffic API contract without a backward-compatibility shim preceding it (causes immediate production failure); a task modifies credentials, secrets, or cryptographic keys without rotation sequencing (security incident risk); two tasks have a cyclic dependency that makes ordering impossible (architectural conflict that must be resolved before decomposition can proceed); or the total task count exceeds 30 without a phased release plan (integration risk — escalate to `architecture-impact-reviewer`).

# Critical Details

- **The most dangerous decomposition failure is a missing migration ordering constraint.** A developer writes the ORM model change (Task A) and the schema migration (Task B) as independent parallel tasks because they are in different files. In the forward direction, both tasks pass in isolation. But in deployment, the ORM code is deployed (reads a column that does not exist yet) — production breaks. In the rollback direction, the schema migration rolls back (drops the column) while ORM code still references it — rollback breaks. The decomposition must represent the ordering constraint explicitly.
- **File-scope reservation prevents merge conflicts in multi-agent execution.** When two agents both edit the same file (e.g., a constants file, an API router, an ORM model) without reservation, the second merge always produces conflicts. The decomposition must ensure that at most one agent "owns" any given file at any point in the execution graph.
- **Verification criteria must be checkable by a different agent than the one that executed the task.** A verification criterion of "looks good" is not a criterion — it is a deferral. Verification must be: executable (run the migration and check the schema diff), observable (the endpoint returns the expected response), or measurable (the test suite passes with 0 failures). This allows a review agent or human reviewer to independently confirm completion.
- **Rollback notes for database migrations must distinguish between schema-safe and data-destructive rollbacks.** Adding a nullable column is safe to roll back (DROP COLUMN, no data to preserve). Dropping a column, transforming existing data, or denormalizing data are irreversible without a prior backup or snapshot. The task record must categorize which rollback type applies and gate the irreversible ones with an explicit approval requirement.

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

# Output Contract

Return a task DAG with:

- `tasks` (per task: id, title, goal, inputs, allowed_files, dependencies, parallel_group, verification, done_condition, rollback_notes, review_evidence, safety_flag)
- `dependency_graph` (edges: task_id → task_id with dependency type)
- `parallel_groups` (named groups of tasks with no inter-dependency and non-overlapping file scopes)
- `critical_path` (minimum serialized execution sequence; total estimated time)
- `safety_flags` (list of tasks with irreversible operations; approval requirements)
- `migration_ordering` (explicit forward and rollback ordering for all schema and data migrations)
- `phased_release_plan` (if applicable: deploy phase 1, validate, deploy phase 2…)
- `cycle_check` (confirmation that the DAG is acyclic; or list of cycles to resolve)

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

# Used By

- task-dag-planner

# Handoff

Hand off to `context-packaging` for assembling task execution context; `test-strategy` for per-task test requirements; `release-rollback` for deployment sequence and rollback design; `code-review` for per-task review criteria.

# Completion Criteria

The capability is complete when **the dependency graph is explicit, parallelizable work is identified, file scopes do not conflict across parallel tasks, all safety tasks precede dependents, and every task has an independently verifiable done condition and a rollback or recovery path**.
