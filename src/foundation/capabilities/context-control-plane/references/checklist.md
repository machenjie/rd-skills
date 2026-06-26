# Context Control Checklist

- Choose `budget_mode`: `minimal`, `single-stage`, `staged-plan`, or `full`.
- Record why each selected capability and reference is needed.
- Record skipped relevant references and why they are safe to skip or remain residual risk.
- Use repository graph, generated reports, and prior summaries as selectors, then read current source directly.
- Bound tool output to command, outcome, relevant excerpt, artifact path, and excluded-output rationale.
- Preserve route, stage, changed paths, validation, review, open questions, and residual risk after compaction.
- Rebuild route assumptions after branch switch, merge, rebase, or route repair.
- Exclude raw prompts, secrets, environment values, full command output, full diffs, full files, personal archives, and private mapping artifacts.
- Track selected/skipped reference counts and token/turn fields, using `not_collected` when exact values are unavailable.
- State what context evidence proves, what it does not prove, validation limits, rollback or reroute note, and next gate.
