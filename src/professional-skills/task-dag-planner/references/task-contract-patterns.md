# Task Contract Patterns

Owner: `task-dag-planner` in read/search-only `analysis-agent` mode after an accepted source-backed Engineering Brief. Load this reference only for two or more real tasks; return a Direct Task Capsule for one bounded task. It does not authorize file edits, dispatch, or machine-managed task state.

## Executable Node Contract

| Field | Required content |
| --- | --- |
| Identity, goal, and owner | One Task ID, observable goal, accountable Owner, and reviewable Expected Output. |
| Inputs | For a fresh-agent task, list the exact applicable source, configs, contracts, generated artifacts, callers, tests, and predecessor outputs whose current state can change execution or verification; omit categories that do not exist or cannot affect the task. |
| Scope and non-goals | Exact read/write paths or resources, public/internal visibility, shared-write risk, and forbidden scope. |
| Reuse and placement | Existing pattern/candidate, rejected locations, dependency direction, and why new structure is or is not needed. |
| Acceptance | Falsifiable behavior, invariant, compatibility, and rejection condition owned by the accepted Brief. |
| Verification and evidence | Literal safe command/check, Evidence Requirements, result, artifact, freshness, scope, and proof limit. |
| Rollback and stop | Revert/forward-fix/manual owner, irreversible limit, and facts that stop execution. |
| Scheduling and review | Dependencies, Parallel Safety, Workspace Requirement, Integration Owner, Review Owner, Skills, and stop conditions. |

## Split, Dependency, And Workspace Rules

- Split when migration, public contract, authorization, UI behavior, data backfill, release, documentation, ownership, validation, rollback, or specialized review has a distinct blocking boundary. Keep together only when a split creates artificial handoff and one owner/reviewer can verify the same artifact.
- Each DAG edge requires a concrete downstream blocker. Blockers may arise from required artifacts, accepted contracts, schema or data availability, shared resources, validation results, or release order. Exclude nonblocking sequence preferences.
- Return the First Executable Slice as soon as it is safe, reversible, verifiable, and cannot be invalidated by unresolved analysis. Name critical path and parallel value.
- With shared or unknown workspace isolation, serialize the write tasks in that workspace. Even with isolation, do not parallelize tasks that share files, schemas, public contracts, migrations, generated outputs, fixtures, lockfiles, external systems, or later integration assumptions.
- Name an integration/validation boundary and a combined Review Boundary when multiple nodes produce one changed surface; identify covered tasks, final paths, primary Review Skill, and only triggered specialist reviews.

## Natural-Language Shape And Proof Limits

Use the authoritative control-plane Task Contract v2 without adding private
state or JSON graphs. Record visible Evidence Ledger entries for graph claims.
Replace placeholders such as TBD, “write tests,” “handle edge cases,” “similar
above,” and “validate it works” with exact behavior, path, evidence, and owner.

A complete plan proves only that the supplied facts form an executable contract. It does not prove source facts, host isolation, commands, implementation, external dependencies, or acceptance are correct. Cycles, unknown owners, overlapping writes, vague verification, or production/destructive decisions without user authority block the DAG rather than creating more planning nodes.
