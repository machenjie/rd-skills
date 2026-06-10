# Review Rubric

## Passing Standard

The solution passes when public contract changes are staged compatibly, consumers and unknown risk are analyzed, migration guidance exists, telemetry is available, and rollback is viable.

## Scoring

- 25 percent consumer discovery: current and unknown consumers across mobile, web, backend, SDK, packages, and events are considered.
- 25 percent compatibility: schema evolution, generated clients, old/new fields, and event payload versions are safe.
- 20 percent migration: deprecation window, guide, and consumer notifications are concrete.
- 20 percent telemetry and rollout: old/new usage, rollout, rollback, and cleanup signals are defined.
- 10 percent tests: contract and compatibility tests cover both versions.

## Automatic Failure Conditions

- API, SDK, schema, event, or public export field is renamed directly with no compatibility path.
- Unknown consumer risk is ignored.
- Generated clients break without migration guide.
- Old contract behavior is removed without telemetry.

## Reviewer Notes

Look for expand-contract-change cleanup sequencing. Penalize changes that are technically simple but operationally breaking for consumers.
