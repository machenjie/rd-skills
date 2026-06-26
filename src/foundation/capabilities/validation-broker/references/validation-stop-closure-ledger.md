# Validation Stop Closure Ledger

Use this reference when final handoff, release readiness, repair review, or stop closure needs a structured validation ledger. The ledger prevents partial, stale, or negative evidence from being flattened into a pass.

## Ledger Fields

| Field | Required Content |
| --- | --- |
| `changed_path` | Source, registry, docs, hook runtime, test, fixture, report, generated artifact, package, or install output. |
| `risk_surface` | skill-authoring, runtime-support, release, security, data, integration, generated-artifact, documentation, or no-material-risk. |
| `selected_validator` | Exact command or explicit no-validator rationale. |
| `scope` | narrow, module, full, no-validator, or unsupported. |
| `outcome` | passed, failed, stale, partial, not-run, not-verified, or unsupported. |
| `freshness` | after_final_edit, before_final_edit, stale_after_later_edit, source_generated_mismatch, or unknown. |
| `negative_evidence` | failure, skipped check, stale report, blocking warning, missing output, unparseable output, unsupported adapter, or none. |
| `closure_consequence` | ready, repair_required, rerun_required, re-review_required, partial_handoff, blocked, or residual_risk_accepted. |

## Negative Evidence Classification

- **Blocking:** failed validator, stale source validator for final diff, generated artifact without source/build proof, or security/release check skipped for a matching risk surface.
- **Repair-required:** failure has a known owner and a validator that can prove the repaired scope.
- **Irrelevant-with-proof:** failure belongs to an unchanged, excluded surface and a reviewed reason names the boundary.
- **Deferred-with-owner:** command is intentionally not run; handoff names the exact command, owner, reason, and risk.
- **Accepted residual risk:** risk is explicitly accepted by the maintainer or handoff owner with a rollback or follow-up path.

## Stop Closure Rules

1. Closure is `passed` only when every material changed path has current validator evidence or a valid no-validator rationale.
2. Any blocking negative evidence makes closure `failed`, `stale`, `partial`, `not-run`, `not-verified`, or `unsupported` until repaired or explicitly accepted.
3. A later unrelated pass does not erase an earlier failure; mark the failure repaired, irrelevant-with-proof, deferred-with-owner, or still blocking.
4. Tool, connector, scanner, release, package, install, and security-sensitive validation must include permission/sandbox boundary and output redaction limits.
5. Final handoff names rollback as reverting the target source/reference changes and rerunning the mapped validators.

## Handoff Template

```yaml
validation_stop_closure_ledger:
  changed_paths: []
  validator_scope: narrow
  commands_current: []
  commands_stale_or_not_run: []
  negative_evidence: []
  graph_memory_trajectory_coupling: []
  closure_status: passed
  evidence_limits: []
  rollback_note: revert target source/reference changes and rerun mapped validators
  residual_risk: []
  next_owner: null
```
