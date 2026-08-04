# Benchmark Prompt

## Task

Diagnose a failing integration test from repository evidence. Do not edit any
file, install anything, or attempt a repair.

## Context

The integration test fails with `ECONNREFUSED 127.0.0.1:5432`. The starter
repo includes a test harness, database config, and fixture setup. A weak agent
response says postgres is probably not running locally and stops there.

## Requirements

- Treat the error message as a symptom, not a diagnosis.
- Inspect the test harness, database configuration, fixture setup, and relevant
  logs before naming a cause.
- Produce a verified-cause statement with confirming and counter-evidence.
- Identify the smallest cause-backed repair boundary, but leave implementation
  to a later task.
- Cite the exact source/config/log locations that confirm the diagnosis.

## Constraints

- Do not tell the user to restart services without first inspecting repo-owned
  setup and configuration.
- Do not skip the failing integration path by converting it to a mocked unit test.
- Do not modify the workspace, including source, tests, config, fixtures, or docs.

## Deliverables

- Verified-cause statement and evidence inventory.
- A bounded repair recommendation and a validation plan for a later task.

## Completion Evidence

- Read-only inspection evidence from the supplied source, config, fixture, and log.
- Diagnosis record showing symptom, hypothesis tested, method, verified cause,
  counter-evidence, and residual risk.
- No unsupported environment-blame language and no workspace changes.
