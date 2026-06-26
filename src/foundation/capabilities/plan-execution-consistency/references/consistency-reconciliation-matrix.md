# Consistency Reconciliation Matrix

Use this reference when final handoff must reconcile a plan, task DAG, route manifest, actual diff, validation order, review scope, graph/memory/trajectory evidence, generated artifacts, docs, release artifacts, install outputs, and residual risk.

## Variance Status

| Status | Meaning | Required Handoff |
| --- | --- | --- |
| matched | Planned file/action appears in final diff or command ledger. | State validation evidence and proof limit. |
| extra | Final diff includes unplanned file/action. | Explain rationale, owner, review scope, and validation impact. |
| missing | Planned file/action was not completed. | Mark deferred, blocked, not done, or not verified; avoid completion claim. |
| renamed | Path or artifact moved. | Name old/new path, compatibility impact, review scope, and validator. |
| generated | File is generated, copied, packaged, or installed output. | Name source-of-truth, generator/build command, and runtime profile. |
| deleted | File/action was removed from final state. | Name deletion rationale, caller/search evidence, rollback, and review status. |
| deferred | Accepted plan item intentionally postponed. | State owner, reason, due gate, and residual risk. |
| abandoned | Plan route was replaced by a different route. | State route repair reason, old evidence limit, and new owner. |
| not verified | Evidence does not prove whether the item is complete. | State missing evidence, next validator/reviewer, and blocked or partial closure. |

## Reconciliation Dimensions

| Dimension | Required Comparison | Failure Signal | Next Gate |
| --- | --- | --- | --- |
| Requirement and non-goal | Original request, accepted assumptions, plan item, changed behavior. | Implementation satisfies an invented plan or adds out-of-scope behavior. | `change-impact-analyzer` or owner skill. |
| Source diff | Planned paths/actions versus final changed paths/actions. | Extra, missing, deleted, or renamed files lack rationale. | `repository-context-map`. |
| Generated and runtime artifacts | Source-of-truth, generator/build command, runtime profile, generated outputs. | Generated-only edit or stale dist/package/install output. | `repository-graph-analysis`, `delivery-release-gate`. |
| Validation | Command, outcome, covered paths, later edits, broker result. | Stale, partial, failed, not-run, unsupported, or outcome missing. | `validation-broker`, `quality-test-gate`. |
| Review and repair | Reviewer scope, findings, repair files, re-review status. | Repair after review or approval without file scope. | `ai-code-review-refactor`. |
| Graph freshness | Current graph/source slice, omitted edges, generated/test edges. | Stale graph or missing test edge drives closure. | `repository-graph-analysis`. |
| Memory status | Accepted/rejected/stale memory claims and projection limits. | Memory treated as current source truth. | `project-memory-governance`. |
| Trajectory order | Read/plan/edit/review/validation/build/handoff order. | Edit-before-read, validation-before-final-edit, repeated same-path retry. | `execution-trajectory-analysis`. |
| Tool permission | Risk class, sandbox/approval, target boundary, rollback. | Unplanned risky command or write lacks record. | `agent-tool-permission-sandbox`. |
| Handoff wording | Final claim versus evidence limits and residual risk. | Done/validated/all-passed claim exceeds proof. | `agent-execution-discipline`. |

## Freshness Rules

| Evidence | Current Only If | Downgrade When |
| --- | --- | --- |
| Source read | It covers the final edited source-of-truth path. | Later edits, generated replacement, or route change changed the target boundary. |
| Validation | It ran after final material edits and covers changed paths/risk surface. | Any covered source, registry, report, generated output, fixture, package, or validation input changed later. |
| Review | Reviewer saw the final diff or the repaired area after repair. | Repair changed files after approval or approval scope is unnamed. |
| Graph | Graph slice is refreshed or direct-source fallback confirms key edges. | Reports, registries, generated outputs, memory, or source changed after graph collection. |
| Memory | Current source confirms each behavior-critical memory claim. | Memory is stale, unclassified, privacy-sensitive, or contradicted by source. |
| Generated artifact | Source, generator command, and runtime profile match final output. | Generated output changed without source/build proof. |

## Closure Decisions

| Decision | Allowed When | Handoff Requirement |
| --- | --- | --- |
| ready | Plan, final diff, validation, review, generated/source status, and residual risk reconcile. | State fresh validation, proof limits, rollback, and remaining low residual risk. |
| partial | Some planned work is done but scoped gaps remain accepted. | Name completed scope, not-run scope, owner, and residual risk. |
| not verified | Work may be done but evidence is insufficient. | Do not claim completion; state missing validator/review/source proof. |
| needs validation | Final material edits lack current mapped validation. | Name exact command/gate and covered paths. |
| needs re-review | Repair or unreviewed variance exists. | Name reviewer, paths, finding or variance requiring review. |
| needs source reread | Plan/graph/memory is stale or source-of-truth is uncertain. | Name source files and generated/artifact boundary to inspect. |
| needs plan repair | Actual route no longer matches accepted plan. | Name old plan, new evidence, and owner for route repair. |
| blocked | Required owner, approval, source, validator, or rollback is unavailable. | Name blocker, owner, residual risk, and safe rollback/not-run state. |

## Handoff Template Fields

Use these fields for a concrete report:

```yaml
plan_execution_consistency_report:
  mode_selected: handoff decision
  boundaries_inspected:
    source: []
    generated_outputs: []
    reports: []
    registries: []
    graph_memory_trajectory: []
    skipped_with_reason: []
  plan_summary:
    planned_actions: []
    planned_files: []
    acceptance_signal: ""
    validation_signal: ""
  actual_change_inventory:
    changed_files: []
    generated_files: []
    command_classes: []
  variance_table:
    - item: ""
      status: matched
      rationale: ""
      owner: ""
      review_status: ""
      validation_impact: ""
  validation_freshness:
    commands: []
    stale_or_not_run: []
    proof_limits: []
  review_and_repair_scope:
    reviewer: ""
    covered_paths: []
    repair_rereview_status: ""
  graph_memory_trajectory_coupling:
    accepted_claims: []
    rejected_or_stale_claims: []
    closure_consequence: ""
  closure_decision: ready
  residual_risk: ""
  rollback_note: ""
  next_owner: ""
```

## Closure Checks

1. Every changed behavior maps to a requirement, acceptance criterion, accepted plan item, or explicit non-goal.
2. Validation runs after the final material edit or is labeled stale, partial, not-run, failed, unsupported, or not verified.
3. Review approval covers the final diff; repair after review requires targeted re-review.
4. Docs, registries, generated artifacts, install packages, runtime profiles, and rollback notes are reconciled when affected.
5. Graph, memory, trajectory, workflow, tool permission, and validation broker evidence are accepted, rejected, or downgraded before closure.
6. The final response states only evidence-backed completion, with unknowns, validation limits, residual risk, rollback note, and next gate.
