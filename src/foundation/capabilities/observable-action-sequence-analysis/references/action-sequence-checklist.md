# Observable Action Sequence Analysis Checklist

Use observable actions only: dispatch, read/search, edit, command result,
validation, review, repair, re-review, progress, and closure.

- Measure time or steps to first productive action and first edit.
- Count control turns, subagents, duplicate reads, loaded Skills, and context
  size.
- Detect repeated same-scope analysis, edit before evidence, stale validation,
  changed paths without type-appropriate evidence, and repair without fresh affected validation.
- Treat absent re-review as a gap only for a new material question needing independent judgment or an unresolved required review.
- Separate deterministic fixtures from live-agent measurements.
- State collection gaps without inferring efficiency gains from structural
  compliance alone.
