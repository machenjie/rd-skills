# Test Suite

Runs the starter repo validation and assertion files. Candidate evaluation requires bounded compaction evidence in `COMPACTION_CONTEXT.json`.

## Required Checks

- Validate the starter repository behavior.
- Inspect `COMPACTION_CONTEXT.json` for required preserved context fields.
- Reject self-reported markdown-only evidence.
- Reject privacy leaks and stale validation claims.

## Fixtures

- `starter-repo/compaction_workflow.py`
- `starter-repo/tests/test_compaction_workflow.py`
- Candidate-produced `COMPACTION_CONTEXT.json`

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Missing post-compact continuation evidence fails.
- Missing validation freshness or review findings after compaction fails.
- Raw prompt, command output, secret, environment variable, full diff, full file content, or local absolute path persistence fails.
