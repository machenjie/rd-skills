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

- Each node is one complete semantic change.
- Each Task has exactly one Primary Professional Skill.
- Modifications that jointly satisfy one Acceptance stay together.
- Co-dependent modifications stay together.
- Modifications with one natural validation boundary stay together.
- Materially different Primary Professional Skills split into separate Tasks.
- File, function, code layer, test, or edit step alone does not split a Task.
- Review and risk boundaries do not redefine the Task boundary.
- Each DAG edge requires a concrete downstream blocker. Blockers may arise from required artifacts, accepted contracts, schema or data availability, shared resources, validation results, or release order. Exclude nonblocking sequence preferences.
- Return the First Executable Slice as soon as it is safe, reversible, verifiable, and cannot be invalidated by unresolved analysis. Name critical path and parallel value.
- With shared or unknown workspace isolation, serialize the write tasks in that workspace. Even with isolation, do not parallelize tasks that share files, schemas, public contracts, migrations, generated outputs, fixtures, lockfiles, external systems, or later integration assumptions.
- Name integration/validation and minimum sufficient Review Boundaries.
- Related nodes default to one combined Review Boundary.
- Reserve intermediate review for a concrete public-contract/schema/protocol,
  migration/data, security/privacy, transaction/concurrency/persistence,
  material-rework, independent-integration, L5, or explicit professional gate.
- For each Review Boundary, identify Covered Task IDs, final paths, Effective
  Level, required Review Skills, professional-risk dimensions, and triggered
  Specialist reviews.
- Combined review preserves each Task Primary Skill.
- Task nodes retain only required Review Skills, Specialist obligations, and professional-risk dimensions. Review strategy, frequency, assignment scheduling, round identity, and primary-close ordering exist only on the global Review Boundary.
- A boundary has one primary and zero or more specialist assignments. Each assignment names one ID, one role, the review-agent profile, exactly one registered Review Skill, zero to three unique Layer 3 selections routed by that Review Skill from review risk, and bounded scope.
- Review-side Layer 3 is independent from the Tasks' implementation Layer 3; neither equality nor union containment is an obligation.
- All assignments share one Review Round ID. Specialist completion does not increment the round count or close covered Tasks.
- The primary consumes every current required specialist result and emits the only closing artifact. Each covered Task projects that artifact's exact identity, digest, boundary, round, and current generation.
- Any scoped material edit invalidates current validation and review evidence only for intersecting scope and transitive Task dependencies. Unaffected current evidence remains reusable.

## Natural-Language Shape And Proof Limits

Use the authoritative control-plane Task Contract v2 without adding private
state or JSON graphs. Record visible Evidence Ledger entries for graph claims.
Replace placeholders such as TBD, “write tests,” “handle edge cases,” “similar
above,” and “validate it works” with exact behavior, path, evidence, and owner.

A complete plan proves only that the supplied facts form an executable contract. It does not prove source facts, host isolation, commands, implementation, external dependencies, or acceptance are correct. Cycles, unknown owners, overlapping writes, vague verification, or production/destructive decisions without user authority block the DAG rather than creating more planning nodes.
