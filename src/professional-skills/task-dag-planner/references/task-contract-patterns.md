# Task Contract Patterns

Use this reference after an accepted source-backed Engineering Brief when two or
more real tasks need an executable dependency graph. A single bounded task does
not need a DAG. Planning does not itself authorize implementation, production
mutation, or machine-managed task state.

## Executable Node Contract

| Field | Required content |
| --- | --- |
| Identity, goal, and owner | One Task ID, observable goal, accountable Owner, and reviewable Expected Output. |
| Inputs | For a fresh implementer, list the exact applicable source, configs, contracts, generated artifacts, callers, tests, and predecessor outputs whose current state can change execution or verification; omit categories that do not exist or cannot affect the task. |
| Scope and non-goals | Exact read/write paths or resources, public/internal visibility, shared-write risk, and forbidden scope. |
| Reuse and placement | Existing pattern/candidate, rejected locations, dependency direction, and why new structure is or is not needed. |
| Acceptance | Falsifiable behavior, invariant, compatibility, and rejection condition owned by the accepted Brief. |
| Verification and evidence | Literal safe command or check, observable normal, invalid, boundary, and forbidden outcomes, result, artifact, freshness, scope, and proof limit. |
| Rollback and stop | Revert/forward-fix/manual owner, irreversible limit, and facts that stop execution. |
| Scheduling and review | Dependencies, parallel safety, workspace requirement, integration owner, review owner, required capabilities, and stop conditions. |

## Split, Dependency, And Workspace Rules

- Each node is one complete semantic change.
- Modifications that jointly satisfy one Acceptance stay together.
- Co-dependent modifications stay together.
- Modifications with one natural validation boundary stay together.
- Materially different professional capabilities split into separate Tasks.
- File, function, code layer, test, or edit step alone does not split a Task.
- Review and risk boundaries do not redefine the Task boundary.
- Each DAG edge requires a concrete downstream blocker. Blockers may arise from required artifacts, accepted contracts, schema or data availability, shared resources, validation results, or release order. Exclude nonblocking sequence preferences.
- Preserve the accepted First Executable Slice. If the Brief has not selected
  one, recommend the earliest safe, reversible, verifiable node that unresolved
  analysis cannot invalidate. Name the critical path and parallel value.
- With shared or unknown workspace isolation, serialize the write tasks in that workspace. Even with isolation, do not parallelize tasks that share files, schemas, public contracts, migrations, generated outputs, fixtures, lockfiles, external systems, or later integration assumptions.
- Name integration/validation and minimum sufficient Review Boundaries.
- Related nodes default to one combined Review Boundary.
- Reserve intermediate review for a concrete public-contract/schema/protocol,
  migration/data, security/privacy, transaction/concurrency/persistence,
  material-rework, or independent-integration risk.
- For each Review Boundary, identify covered Task IDs, final paths, professional
  risk dimensions, required evidence, and any independent specialist review.
- Keep review strategy, cadence, assignment, and closure ordering on the Review
  Boundary rather than duplicating them across task nodes.
- The accountable review owner consumes every required specialist result and
  emits the closing decision for the boundary.
- Any scoped material edit invalidates current validation and review evidence
  for intersecting scope and transitive task dependencies. Unaffected current
  evidence remains reusable only when its source and assumptions are unchanged.

## Natural-Language Shape And Proof Limits

Use the repository's accepted Task Contract shape without inventing private
state or opaque machine graphs. Record visible Evidence Ledger entries for graph claims.
Replace placeholders such as TBD, “write tests,” “handle edge cases,” “similar
above,” and “validate it works” with exact behavior, path, evidence, and owner.

A complete plan proves only that the supplied facts form an executable contract. It does not prove source facts, host isolation, commands, implementation, external dependencies, or acceptance are correct. Cycles, unknown owners, overlapping writes, vague verification, or production/destructive decisions without user authority block the DAG rather than creating more planning nodes.
