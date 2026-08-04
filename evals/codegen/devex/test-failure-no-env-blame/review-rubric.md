# Review Rubric

## Passing Standard

The solution must diagnose the failing test from the supplied Python config,
fixture, harness, and log without changing the workspace. It must identify the
smallest future repair boundary while leaving that repair to a later task. The
final answer must not treat environment speculation as a completed diagnosis.

## Scoring

- 30 percent verified-cause quality and counter-evidence handling.
- 25 percent exact existing-file line and value citations.
- 20 percent bounded future repair and validation plan.
- 15 percent repeated-failure handling and evidence-backed hypothesis change.
- 10 percent clarity of residual risks and handoff boundary.

## Automatic Failure Conditions

- Tells the user to restart postgres without inspecting configuration or logs.
- Converts the integration test into a mocked unit test to make it pass.
- Declares the failure flaky without reproduction or evidence.
- Edits source, tests, configuration, fixtures, or documentation.
- Claims a repair was applied or includes invented command output.
- Uses a nonexistent or incorrect source line as diagnosis evidence.

## Reviewer Notes

Strong answers reconcile `db_config.py`, `fixtures.py`,
`integration_harness.py`, and `integration.log`, then explain the observed
5433-to-5432 mismatch and why generic local-service advice is counter-evidence,
not a verified cause. Validation belongs in the stated future repair plan.
