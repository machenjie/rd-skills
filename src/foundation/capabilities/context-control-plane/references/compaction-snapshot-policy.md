# Compaction Snapshot Policy

A compaction snapshot preserves only state needed to continue safely after context loss.

## Snapshot Fields

- current goal and non-goals
- selected route, stage, skills, capabilities, domain extensions, gates, and references
- changed paths and material generated artifacts
- decisions made and rejected alternatives
- validation commands, outcomes, freshness, and negative evidence
- review findings, accepted risks, and open questions
- privacy exclusions and tool-output boundaries
- context-control budget mode, selected/skipped reference counts, over-budget
  findings, JIT retrieval requirement, and tool-output boundary requirement
- selected reference policy, omitted context records, branch route-repair
  summaries, and runtime metadata gaps such as unavailable token or retained
  entry identifiers
- next gate, owner, rollback or reroute note, and residual risk

Do not preserve hidden reasoning, raw prompts, full logs, full diffs, environment values, secrets, or unrelated source content.

New snapshots use `schema_version: 2`. Explicit `schema_version: 1` snapshots
remain valid when they satisfy the original required context fields.
