# Plan Execution Handoff Ledger

Use this compact ledger when final handoff needs a precise closure record but not the full reconciliation matrix.

```yaml
plan_execution_handoff:
  mode_selected: handoff decision
  planned_scope:
    actions: []
    files: []
    non_goals: []
  actual_scope:
    changed_files: []
    generated_or_report_files: []
    extra_or_missing_items: []
  validation:
    targeted:
      command_or_results: ""
      status: pass | fail | stale | partial | not_run
      proves: ""
      does_not_prove: ""
    full:
      command_or_results: ""
      status: pass | fail | stale | partial | not_run
      proves: ""
      does_not_prove: ""
  review:
    findings: []
    repair_trace: []
    rereview_status: pass | fail | not_run | not_needed
  generated_source_alignment:
    source_paths: []
    build_or_generator: ""
    runtime_profile: ""
  rollback_note: ""
  residual_risk:
    owner: ""
    reason: ""
  next_queue_or_gate: ""
```

## Ledger Rules

- Use `partial` rather than `pass` when a command covers only targeted paths.
- Use `not_needed` for re-review only when there were no findings or repair edits after review.
- Name report or result paths instead of pasting full command output.
- State the next queue or next gate when the broader goal is still active.
