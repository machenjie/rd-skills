# Permission Validation Freshness

Load this reference when command permission, sandbox state, generated outputs, validation order, execution trajectory, or plan-execution consistency can make earlier evidence stale.

## Freshness Rules

| Event | Freshness Impact | Required Response |
| --- | --- | --- |
| Command arguments or target path change after approval | Permission evidence no longer matches the executed action. | Reclassify action and update target boundary before execution. |
| Patch/edit after validation | Validation evidence is stale for final material diff. | Rerun mapped validators or disclose stale/not-verified closure. |
| Build/report/dist/install command writes outputs | Local-write evidence extends beyond source markdown. | Map generated outputs to source truth and rerun link/install checks. |
| Repair after review | Review approval no longer covers final diff. | Re-review repaired paths or carry residual risk with owner. |
| Adapter cannot observe outcome or changed paths | Runtime evidence is partial. | Downgrade evidence and attach manual tool record. |
| Failed risky command retried with same route | Same-path retry risk rises. | Change route after two failures; do not execute a third same-path attempt. |

## Validation Coupling Checklist

- Record the latest material edit before each validator.
- Map each changed path to targeted validators and full AGENTS validation when the change touches skill source, references, registry, build, install, hook runtime, or generated artifacts.
- Treat generated reports and `dist/` as validation outputs unless a maintainer explicitly asks to edit them as source.
- Tie every completion claim to a command that ran after the final material edit.
- When validation cannot run, state not verified, why, exact command, rollback note, and residual risk.
- Compare planned files to actual changed files before handoff.

## Closure States

| State | Meaning |
| --- | --- |
| current-supported | Permission, target, sandbox, validation, and final diff align. |
| current-partial | Some evidence is current but limited to a target or validator subset. |
| stale | A later edit or output write invalidated earlier validation or permission evidence. |
| not-run | Required validator or permission step was not executed. |
| failed | Command or validator returned negative evidence. |
| unsupported | Adapter/tool visibility cannot prove permission, path, outcome, or stop state. |
| rollback-unverified | Revert/restore path exists but was not tested. |

## Compact Record

```yaml
permission_validation_freshness:
  material_edit_order: []
  permission_record_order: []
  validation_ledger:
    - command: ""
      scope: ""
      outcome: passed | failed | not-run | partial
      ran_after_final_edit: true
  generated_outputs: []
  stale_evidence: []
  current_evidence: []
  plan_execution_variance: none | extra_files | missing_files | generated_outputs | stale_validation
  rollback_note: ""
  residual_risk: ""
  next_gate: validation-broker | plan-execution-consistency | quality-test-gate | agent-execution-discipline
```

## Evidence Limits

Fresh validation proves only the checked paths and behaviors at the command scope. It does not prove uninspected external systems, production state, unsupported adapter events, or generated artifacts not covered by the command. Full validation is current only when it completes after the final material diff.
