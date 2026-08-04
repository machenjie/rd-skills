# Observable Action Sequence Analysis Checklist

Use observable actions only: dispatch, read/search, edit, command result,
validation, review, repair, re-review, progress, and closure.

- Measure time or steps to first productive action and first edit.
- Count control turns, subagents, duplicate reads, loaded Skills, and context
  size.
- Detect repeated same-scope analysis, edit before evidence, stale validation,
  unreviewed changed files, and repair without re-review.
- Separate deterministic fixtures from live-agent measurements.
- State collection gaps without inferring efficiency gains from structural
  compliance alone.
