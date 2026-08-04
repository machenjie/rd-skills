# Test Suite

## Required Checks

- Python config and fixture constants are parsed from the supplied files.
- `integration.log` is reconciled with those exact values and its source line.
- The diagnosis records a verified cause, counter-evidence, and future repair plan.
- Workspace before/after manifests are identical and `diff.patch` is empty.

## Fixtures

- `db_config.py` with configured port 5433.
- `fixtures.py` with expected postgres port 5432.
- `integration_harness.py` and `integration.log` showing the pre-test refusal.

## Expected Commands

Run `bash ../test-suite/run.sh` to invoke the benchmark's stdlib Python
assertion. The candidate performs read-only inspection only; it does not run a
repair or paste raw command output.

## Regression Cases

- Skipping the integration fixture should fail review.
- Hardcoding a developer-specific database URL should fail review.
- Environment blame without inspected evidence should fail execution discipline review.
- False line citations, a non-empty diff, or claiming that the fix was applied fail grading.
