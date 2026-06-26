# Workflow Closure State Package

Use this reference when a final handoff, stop decision, release handoff, or blocked state needs a compact workflow closure package. The package keeps route, stage, validation, repair, and residual-risk claims aligned.

## Closure Package Fields

| Field | Required Content |
| --- | --- |
| `route_manifest` | Selected skills, selected capabilities, skipped gates, and runtime profile boundary. |
| `stage_manifest` | Current stage, next stage or closed state, owner, reviewer, and context budget. |
| `changed_scope` | Source files, references, registries, tests, reports, generated artifacts, packages, or install outputs changed. |
| `validation_scope` | Commands run, outcome, covered paths, uncovered paths, freshness, and evidence limits. |
| `review_scope` | Reviewer or gate, approval scope, findings, repairs, and re-review status. |
| `tool_boundary` | Shell/connector/scanner/release action class, sandbox or permission state, redaction rule, and revert path. |
| `rollback_note` | Source revert target, generated/report refresh expectation, and validators to rerun. |
| `residual_risk` | Stale, partial, not-run, unsupported, unknown-owner, or accepted-risk items. |

## Closure Status Rules

- `ready`: final material state has current validation, no unresolved findings, and route/stage manifests match changed scope.
- `needs-read`: source, graph, owner, or source-of-truth boundary was not inspected before planning or edit.
- `needs-validation`: mapped validators did not run after final material edit.
- `needs-rereview`: repair or extra diff occurred after review approval.
- `needs-release-gate`: build, install, package, deployment, migration, or generated artifact scope is unresolved.
- `blocked`: required owner input, route repair, third-attempt stop, failed validation, or security/release blocker remains.
- `not-verified`: evidence channel cannot prove the claim or unsupported adapter fields are the only state source.

## Handoff Checklist

1. Restate `changeforge_route` and `changeforge_stage_route` if routed work occurred.
2. Name inspected paths and skipped boundaries with reasons.
3. Map each changed path to current validation or explicit residual risk.
4. State review/repair/re-review status and approval scope.
5. State rollback note and exact next owner when not ready.
