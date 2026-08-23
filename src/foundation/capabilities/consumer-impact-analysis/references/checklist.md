# Consumer Impact Analysis Checklist

- Name the changed endpoint, field, schema, event, webhook, SDK, export, CLI output, config, example, or behavior.
- Inventory direct, generated, inferred, mobile/partner/public, subscriber/job/report/dashboard, docs/example, omitted, and unknown consumers.
- Record searched repositories/graphs, generated artifacts, exports, registries, package metadata, documentation, telemetry, owner evidence, and gaps; local caller search cannot prove absence.
- Classify structure, meaning, validation, defaults, errors, timing/order, persistence, generated output, and rollback.
- Map old/new producers and consumers, old/new code and data, delayed consumers and retained/replayed messages, and generated clients/providers.
- Select additive, bridge/alias, expand/migrate/contract, version, upcaster/adapter, flag/opt-in, dual publish/write, configuration bridge, or no-ship.
- Verify regeneration/compile, event/webhook/CLI mapping, replay, package/schema impact, contract/smoke tests, or owner review.
- Base deprecation/removal on current usage, telemetry window and lag, owner acceptance, migration/Sunset guidance, cleanup owner, and rollback state—not a calendar alone.
- Treat prior evidence as a selector until final source, generated artifacts, fixtures, docs, telemetry, and validation are fresh.
- Close with covered and unknown consumers, what evidence proves and does not prove, residual risk, next owner, and rollback.
