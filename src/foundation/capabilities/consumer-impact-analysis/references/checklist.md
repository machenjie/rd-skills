# Consumer Impact Analysis Checklist

Use this checklist for concrete consumer-impact reviews. Keep routine L1/L2 routing in `SKILL.md`; load deeper references only when compatibility, telemetry, rollout, rollback, or stale-evidence risk needs more detail.

- Name the changed public surface: endpoint, field, schema, event, webhook, SDK method, package export, CLI output, config key, docs/example contract, or observable behavior.
- Classify consumers as known direct, generated, inferred, mobile/partner/public, event subscribers, jobs/reports/dashboards, docs/example users, and unknown.
- Record search scope, repository graph edges, generated artifact list, package metadata, docs/examples, telemetry source, registry source, and omitted boundaries.
- Classify compatibility across structure, meaning, validation, defaults, error behavior, timing/SLA, ordering/pagination, persistence, and rollback.
- Map old producer/new consumer, new producer/old consumer, old code/new data, new code/old data, delayed consumer/retained event, and generated client/provider behavior.
- Choose additive, bridge/alias, expand/migrate/contract, versioned endpoint/schema, upcaster/adapter, feature flag/opt-in, dual publish/write, config bridge, or no-ship.
- State migration docs, owner notification, deprecation/Sunset signal, telemetry threshold, removal owner, and rollback state before approving cleanup.
- Validate changed surfaces with schema/API/export diff, generated-client compile, consumer-driven contract test, fixture replay, downstream smoke, telemetry check, or owner review.
- Treat project memory and repository graph as selectors until current source, generated artifacts, telemetry, and command order confirm freshness.
- Close with what evidence proves, what it does not prove, residual unknown-consumer risk, rollback note, and next gate.
