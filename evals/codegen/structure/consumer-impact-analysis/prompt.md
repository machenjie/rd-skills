# Benchmark Prompt

## Task

Change an API, SDK, schema, and event field from `userName` to `displayName` without breaking existing consumers.

## Context

The starter repository renames the field directly in OpenAPI, generated clients, event payloads, and public exports. Mobile, web, backend, and package consumers may still read the old field, but no one has checked telemetry.

## Requirements

- Identify current consumers and unknown consumer risk.
- Analyze generated clients, mobile, web, backend, SDK/package consumers, schema evolution, and event payload compatibility.
- Provide compatibility strategy, deprecation window, migration guide, telemetry for old/new usage, rollout, and rollback.
- Add tests for old and new field behavior.
- Name residual consumer risk.

## Constraints

- Do not make a direct breaking field rename.
- Do not remove old behavior without telemetry proving unused or accepted risk.
- Do not publish generated-client breaking changes without migration docs.
- Do not ignore unknown consumers.

## Deliverables

- Consumer Impact Report.
- Compatibility and migration plan.
- Deprecation policy and telemetry.
- Rollout, rollback, and tests.

## Completion Evidence

- Old and new field behavior are compatible during the deprecation window.
- Generated clients can be regenerated or migrated safely.
- Telemetry and migration docs support cleanup timing.
