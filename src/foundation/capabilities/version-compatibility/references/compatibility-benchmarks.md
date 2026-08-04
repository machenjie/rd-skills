# Compatibility Benchmarks

Load this reference when public API, SDK, schema, event, config, stored-data, generated-client, or mixed-version rollout compatibility is under review.

## Surface And Dimension Inventory

| Surface | Compatibility question | Evidence |
| --- | --- | --- |
| API/DTO/error/pagination | Can old/new clients send, parse, interpret, and remediate both success and failure contracts? | Schema/API diff, generated client, fixtures, provider/consumer tests. |
| Protobuf/event/webhook | Are identifiers/field numbers, schema modes, signatures, ordering, retries, retention, and replay compatible? | Schema/AsyncAPI/proto diff, registry mode, replay and consumer inventory. |
| Stored data | Can old/new binaries read and write each other’s values during canary and rollback? | Reader-writer matrix, migration/bridge, rollback query. |
| Config/environment | Can rolling binaries handle old/new keys, defaults, precedence, and restart state? | Binary/config matrix and old-key telemetry. |
| SDK/package/CLI | Do source/binary/public exports, stdout/stderr, exit codes, and scripts remain compatible? | Public API/golden diff, semver decision, downstream compile/test. |
| Mobile/partner/public client | Does support cover clients that cannot be force-upgraded? | Version/use telemetry, partner plan, deprecation/sunset signal. |

Review structure, meaning, validation, null/default, error, timing/SLA, ordering/pagination, and persistence/rollback independently; a schema-only diff cannot prove behavioral compatibility.

## Change Classification

| Change | Condition | Mitigation/proof |
| --- | --- | --- |
| Add optional field/operation | Compatible only if semantics/defaults stay additive and consumers tolerate unknowns. | Old client/parser/generated-type proof. |
| Require/remove/rename | Breaking when current producers/consumers depend on old shape. | Bridge/alias, version, deprecation and telemetry-gated removal. |
| Type/format/meaning/default change | Shape may compile while interpretation changes. | New field/version or explicit mapping, migration and consumer acceptance. |
| Validation tightening/relaxing | Rejects prior valid input or weakens current invariants/security. | Producer migration or threat/invariant review. |
| Enum/event expansion | Compatibility depends on exhaustive switches, closed generated types, and unknown handling. | Unknown fixture, dual publish/version, or downstream compile. |
| Timing/order/async change | Clients may rely on timeout, retry horizon, consistency, sort, cursor, or event order. | Behavior/SLO fixtures and migration communication. |

## Mixed-Version And Mitigation Contract

| Path | Pass condition |
| --- | --- |
| Old producer → new consumer | New path accepts old shape/defaults or has deterministic migration/upcaster. |
| New producer → old consumer | Additive/tolerated representation or old path/bridge remains served. |
| Old code → new data/config | Old binary ignores/understands new state or bridge writes old representation too. |
| New code → old data/config | Defaults, dual-read, upcaster, or backfill guard handles old state. |
| Delayed consumer/replay | Compatibility covers the real retention, lag, and replay window. |
| Generated client → provider | Diff/compile/contract proof passes or a version boundary is used. |

Choose additive change, bridge/alias, expand-migrate-contract, version, upcaster/adapter, opt-in flag, dual publish/write, or config bridge from the failing path. Name precedence, atomicity/reconciliation, unknown handling, rollout order, rollback flag, telemetry, and cleanup owner.

## Removal, Freshness, And Proof Limits

- Removal requires current known/unknown consumer inventory, published migration/support obligations where applicable, owner approval, and telemetry that measures the old surface over the relevant client/replay/deploy window. Calendar time alone is not proof.
- Inspect providers/consumers, generated clients, schemas/topics/configs/migrations/packages/docs/tests/jobs/dashboards. Prior “internal only” or “safe enum” claims are leads, not proof.
- Validate old/new fixtures, producer-consumer and reader-writer paths, error/null/default/enum/order cases, generated artifacts, rollout checkpoints, and immediate rollback state after the final change.
- Local search and provider tests do not prove public/mobile/partner clients, delayed events, runtime config, or production rollback; name residual owner.

Route field semantics to `dto-schema-design`, consumer inventory to `consumer-impact-analysis`, executable contracts to `contract-testing`, migrations to `data-migration-design`, and rollout/rollback to `release-rollback`.

Reject “optional is always safe,” “new enum is non-breaking,” docs/calendar-only removal, redeploy-only rollback, 200-only contract tests, config rename without a bridge, or registry defaults chosen without producer/consumer direction.
