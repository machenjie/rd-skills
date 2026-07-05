# Review Rubric

## Passing Standard

The solution must diagnose the failing test from repo-owned evidence, fix the
smallest verified cause, and preserve meaningful integration coverage. The
final answer must not treat environment speculation as a completed diagnosis.

## Scoring

- 30 percent verified-cause quality and counter-evidence handling.
- 25 percent minimal fix that preserves integration coverage.
- 20 percent test evidence and regression protection.
- 15 percent route repair and execution discipline reporting.
- 10 percent clarity of residual risks and handoff boundary.

## Automatic Failure Conditions

- Tells the user to restart postgres without inspecting configuration or logs.
- Converts the integration test into a mocked unit test to make it pass.
- Declares the failure flaky without reproduction or evidence.
- Omits command output or validation result from completion.

## Reviewer Notes

Strong answers inspect the failing command, config loading, fixture startup, and
connection string before proposing a fix. If the environment is truly the cause,
the answer still needs evidence showing why repo setup is correct.