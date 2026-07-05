# Workflow Adapter Trajectory Coupling

Use this reference when workflow state depends on executor adapter limits, trajectory order, repository graph, project memory, or validation broker evidence. These inputs can change the legal next stage but do not replace current source inspection, independent review, or mapped validation.

## Coupling Matrix

| Evidence Source | Accept As | Downgrade When | Legal Stage Effect |
| --- | --- | --- | --- |
| Executor adapter | Supported lifecycle, permission, command class, and tool outcome facts. | Event field is unsupported, missing, partial, or adapter-specific. | Use manual fallback state and mark closure partial or not verified. |
| Execution trajectory | Ordered read, plan, edit, validation, review, repair, stop, and handoff facts. | Event order is missing, edit-before-read appears, or validation predates final edit. | Return to read, validation, repair, or re-review stage. |
| Repository graph | Source-of-truth, owner, generated artifact, and affected-test selectors. | Graph is stale, low confidence, generated-only, or lacks direct test edges. | Require source reread, broader validator, or residual risk. |
| Project memory | Repeat-failure, fragile-path, stale-context, or prior validation-gap signal. | Memory is unconfirmed by current source or privacy-excluded. | Widen graph/read scope or block third same-path retry. |
| Validation broker | Parsed command outcome, scope, freshness, and negative evidence. | Result is stale, failed, partial, not-run, unsupported, or mismatched. | Block closure or return to validation/repair. |

## Decision Rules

1. Treat unsupported adapter fields as evidence limits, not as passed workflow states.
2. Let trajectory order override older validation claims when final edits changed covered paths.
3. Use graph and memory as scope selectors until current source confirms behavior-critical claims.
4. Preserve validation broker negative evidence in the workflow state instead of hiding it behind a later unrelated pass.
5. If evidence sources disagree, choose the most restrictive legal next stage and name the residual risk.

## Output Fields

- `adapter_support`: supported, partial, unsupported, or not-used.
- `trajectory_order`: current, stale, edit-before-read, repair-without-rereview, repeated-failure, or unknown.
- `graph_memory_verdict`: accepted, rejected, stale, selector-only, or not-used.
- `broker_status`: passed, failed, stale, partial, not-run, not-verified, unsupported, or not-used.
- `stage_effect`: allowed, needs-read, needs-validation, needs-repair, needs-rereview, needs-release-gate, blocked, or not-verified.
