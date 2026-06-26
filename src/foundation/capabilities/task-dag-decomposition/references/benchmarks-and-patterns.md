# Task DAG Decomposition Benchmarks and Patterns

Use this reference when a task DAG needs deeper templates, dependency classification, graph-memory-trajectory coupling, or sequencing examples. Keep `SKILL.md` focused on triggers, rules, output, and gates.

## Contents

- [Benchmark Anchors](#benchmark-anchors)
- [Task Record Template](#task-record-template)
- [Dependency Classification Matrix](#dependency-classification-matrix)
- [Graph, Memory, and Trajectory Coupling](#graph-memory-and-trajectory-coupling)
- [Sequencing Decision Tree](#sequencing-decision-tree)
- [Parallelism Review Checklist](#parallelism-review-checklist)
- [Changed Task to Validation Mapping Examples](#changed-task-to-validation-mapping-examples)
- [Anti-Pattern Review](#anti-pattern-review)

## Benchmark Anchors

- PMI PMBOK Work Breakdown Structure: decompose deliverables into assignable, estimable, independently verifiable work packages.
- Trunk-based development: prefer small, frequent, reviewable changes; use feature flags or branch-by-abstraction to keep incomplete work releasable.
- Progressive delivery: decouple deploy from release with flags, canaries, and rollback signals.
- DORA small-batch research: smaller batches correlate with lower change failure and higher deployment frequency.
- Dependency graph formalisms: topological sort, cycle detection, and critical path analysis turn dependency claims into executable order.
- LLM agent task design: bounded context, explicit allowed files, verifiable output, and tool constraints improve agent reliability.

## Task Record Template

```yaml
task_id: "T-012"
title: "Add user_tier column to accounts table"
goal: >
  Add nullable user_tier VARCHAR(20) column to accounts via a backward-compatible
  migration that current code can ignore during rollout.
owner_surface: "data"
inputs:
  - current accounts schema
  - approved user_tier values
files_to_inspect:
  - db/schema.rb
  - app/models/account.rb
allowed_files:
  - db/migrations/20240801_add_user_tier_to_accounts.sql
  - db/schema.rb
reuse_and_placement:
  reuse_candidates:
    - existing additive migration pattern
  placement_decision: "new migration under db/migrations; no shared helper"
dependencies:
  - task_id: "T-010"
    type: "data dependency"
    reason: "field values must be approved before DDL is written"
parallel_group: null
validation_command: "rails db:migrate && rails db:rollback"
expected_output: "migration and rollback exit 0; schema shows nullable user_tier"
done_condition: "migration reviewed, executed on staging-like schema, and rollback tested"
rollback_notes: >
  Down migration drops the nullable column. If production writes user_tier before
  rollback, data owner approval is required because values will be lost.
review_gate:
  reviewer_skill: "data-api-contract-changer"
  evidence: "schema diff and rollback output"
repair_route: "data-migration-design"
safety_flag:
  irreversible: false
  approval_required: false
```

## Dependency Classification Matrix

| Dependency type | Serialization requirement | Common failure if ignored | Evidence |
| --- | --- | --- | --- |
| Data dependency | Producer task before consumer task. | Consumer fails because required artifact or decision is absent. | Produced artifact, owner decision, or schema diff. |
| File-scope conflict | Serialize or merge into one node when allowed files overlap. | Merge conflict or overwritten change. | Shared-file scan and allowed_files comparison. |
| Deployment dependency | Provider/service/infrastructure before dependent deployment. | Startup or runtime failure during rollout. | Deploy order and compatibility window. |
| Test dependency | Setup/migration/seed before integration or E2E verification. | Test fails for missing data or schema. | Test fixture and setup command. |
| Migration forward ordering | Expand migration before code that requires new schema. | Code reads missing column/table. | Expand/code/contract plan. |
| Migration rollback ordering | Backward-compatible code before schema contraction. | Rollback drops state still read by live code. | Rollback sequence and old/new coexistence check. |
| Graph freshness dependency | Graph refresh or direct source check before relying on graph edge. | Plan follows stale owner or generated artifact edge. | Graph timestamp/hash or direct-source fallback. |
| Trajectory repair dependency | Re-review after repair before downstream unblock. | Fixed node changes after approval without reviewer coverage. | Repair ledger and re-review result. |

## Graph, Memory, and Trajectory Coupling

- Repository graph helps select source files, callers, generated artifacts, tests, and possible validation candidates. It must remain bounded to the task and confirmed by direct source inspection for behavior-critical claims.
- Project memory helps identify fragile files, previous failures, stale assumptions, and repeated bad routes. It can widen review or validation scope but cannot become source truth without maintainer-approved promotion.
- Execution trajectory helps decide whether validation is fresh, whether repair needs re-review, and whether a repeated-failure route must change.
- A DAG should record each graph, memory, or trajectory claim as accepted, rejected, stale, or not verified, then state how it changed nodes, edges, validation, or residual risk.

## Sequencing Decision Tree

```
Does the change include data/schema migration?
  YES -> Expand migration -> compatibility code -> validation -> contract cleanup.
Does it include a breaking API or event contract?
  YES -> Add compatible version/shim -> migrate consumers -> verify -> remove old path.
Does it include feature flag or config behavior?
  YES -> Register flag/default -> implement behind flag -> staged rollout -> cleanup.
Does it include secrets or credential rotation?
  YES -> Provision new secret -> dual-read or staged deploy -> rotate -> revoke old secret.
Does it include previous failed validation or repair?
  YES -> Add diagnostic/repair node -> re-review node -> fresh validation node.
Can nodes run in parallel?
  ONLY IF -> no dependency edge, no shared mutable file/resource, and independent validation.
```

## Parallelism Review Checklist

- Compare `allowed_files` for exact overlap and likely generated-output overlap.
- Check shared database tables, queues, topics, configs, fixtures, feature flags, API contracts, and package manifests.
- Check whether one task changes validation inputs for another task.
- Do not parallelize tasks that share a migration chain, generated file, public contract, global config, or common utility unless an explicit owner serializes the shared surface.
- Re-run the parallelism review after any task scope changes.

## Changed Task to Validation Mapping Examples

- Migration node -> migration forward/rollback command, schema diff, data-loss approval if destructive.
- API compatibility node -> contract test, generated-client check, consumer inventory.
- Feature flag node -> default-off config check, rollout metric, cleanup task deadline.
- Parallel group -> shared-file/resource scan and non-overlap proof.
- Graph claim -> current source inspection or graph refresh marker.
- Memory claim -> accepted/rejected source check and residual risk if stale.
- Repair route -> repair evidence plus independent re-review.
- Skipped task scope -> explicit non-goal, owner, and not-present validation.

## Anti-Pattern Review

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Flat checklist with no edges. | Execution order is ambiguous. | Add dependency graph and topological order. |
| "Implement backend changes." | Migration, auth, API, and tests hide in one node. | Split by risk domain and review artifact. |
| Two parallel tasks edit the same router/config. | Merge conflict or lost change. | Serialize or assign one owner node. |
| Rollback note says "revert commit." | Data, flags, or external state may already have changed. | Add concrete rollback or recovery procedure. |
| Graph says generated file is target. | Source-of-truth may be missed. | Identify source file and build command first. |
| Memory says previous validation passed. | Validation may be stale. | Re-run or mark not verified after current edits. |
| Repair changes task output after approval. | Reviewer did not cover final work. | Add re-review node before closure. |
