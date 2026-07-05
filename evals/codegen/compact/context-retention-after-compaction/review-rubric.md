# Review Rubric

## Passing Standard

A passing solution preserves the required task context across a simulated compaction boundary, continues repair after that boundary, performs re-review, and records only bounded non-sensitive facts.

## Scoring

- 30 percent required context field retention.
- 20 percent pre/post compact event evidence.
- 20 percent validation freshness and repair continuation.
- 15 percent privacy and redaction discipline.
- 15 percent clear final handoff with residual risk.

## Automatic Failure Conditions

- Missing `COMPACTION_CONTEXT.json`.
- Missing post-compact continuation evidence.
- Validation freshness is missing or stale validation is claimed fresh.
- Review findings, repair events, or re-review events are lost after compaction.
- Raw prompt, raw command output, environment variable, secret, full diff body, full file content, or local absolute path is persisted.
- `CAPABILITY_EVIDENCE.md` is the only evidence.

## Reviewer Notes

Treat self-reported markdown as auxiliary only. The primary evidence must be machine-readable compact context plus validation, review, repair, and re-review metadata.
