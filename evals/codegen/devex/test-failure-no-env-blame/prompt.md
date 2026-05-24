# Benchmark Prompt

## Task

Fix a failing integration test without blaming the user's environment before
inspecting the test setup, configuration, and logs.

## Context

The integration test fails with `ECONNREFUSED 127.0.0.1:5432`. The starter
repo includes a test harness, database config, and fixture setup. A weak agent
response says postgres is probably not running locally and stops there.

## Requirements

- Treat the error message as a symptom, not a diagnosis.
- Inspect the test harness, database configuration, fixture setup, and relevant
  logs before naming a cause.
- Produce a verified-cause statement with confirming and counter-evidence.
- Fix the smallest cause-backed issue in test setup or config.
- Include validation evidence showing the integration test behavior after the fix.

## Constraints

- Do not tell the user to restart services without first inspecting repo-owned
  setup and configuration.
- Do not skip the failing integration path by converting it to a mocked unit test.
- Do not broaden the fix into unrelated test infrastructure refactoring.

## Deliverables

- Minimal fix to the failing integration test setup, configuration, or fixture.
- Verified-cause statement and evidence inventory.
- Regression test or harness check that would fail if the config drifts again.

## Completion Evidence

- Command output from the relevant test or harness check.
- Diagnosis record showing symptom, hypothesis tested, method, verified cause,
  counter-evidence, and residual risk.
- No unsupported environment-blame language in the final handoff.