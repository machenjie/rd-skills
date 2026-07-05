# Consumer Impact Benchmarks And Patterns

Use this reference for L3+ public API/SDK/schema/event/export changes, generated-client impact, unknown consumers, compatibility migrations, telemetry gates, deprecation/removal, mixed-version rollout, rollback, or mobile/partner lag.

## Benchmark Anchors

- **Semantic Versioning 2.0.0:** breaking public API changes require major versioning or explicit compatibility bridge.
- **Consumer-driven contract testing:** active consumer expectations must be verified by the provider before deployment.
- **OpenAPI / AsyncAPI / Protobuf breaking-change detection:** schema diff tools catch structural changes but not all semantic, default, or rollout risks.
- **Schema registry compatibility modes:** BACKWARD, FORWARD, and FULL compatibility must match producer/consumer rollout order.
- **RFC 8594 Sunset header:** public deprecation needs machine-readable retirement signaling and migration guidance.
- **Expand/contract rollout:** deploy additive compatibility first, migrate consumers, then remove old behavior only after evidence.
- **Generated client governance:** generated SDKs, package exports, examples, and compile checks are consumer evidence, not incidental artifacts.
- **Telemetry-gated deprecation:** old/new usage and error telemetry should drive removal readiness where available.

## Consumer Inventory Matrix

| Consumer Class | Examples | Evidence |
| --- | --- | --- |
| Known direct | Frontend app, backend service, CLI caller, import site | Search result, call graph, owner confirmation |
| Generated | SDK, typed client, protobuf/OpenAPI/AsyncAPI output | Generator config, source spec hash, generated diff, compile |
| Public/partner/mobile | Published API, partner webhook, app-store client | API key/client id/version telemetry, support window |
| Event/job/report | Subscriber, batch job, dashboard, analytics query | Topic/consumer group, job definition, dashboard query |
| Docs/examples | Copied snippets, fixtures, public examples | Docs search, example tests, release notes |
| Unknown | Dynamic calls, external users, package downloads | Telemetry, registry/package metadata, residual risk owner |

## Compatibility Classification Matrix

| Dimension | Consumer Risk | Required Evidence |
| --- | --- | --- |
| Structure | field/endpoint/event/export shape changes | schema/API/export diff and generated-client compile |
| Meaning | same shape with changed semantics or units | before/after semantics and consumer acceptance |
| Validation | requiredness, enum, regex, min/max, unknown-field policy | old/new request fixtures and validation diff |
| Defaults | omitted fields now behave differently | default map, opt-in bridge, telemetry impact |
| Error behavior | status, retryable flag, problem body, error code | error contract tests and client remediation map |
| Timing/order | pagination, ordering, async/sync, timeout, retention | ordering/pagination/replay fixtures |
| Persistence | new writes old code cannot read after rollback | old/new reader-writer and rollback validation |

## Mixed-Version Rollout Matrix

| Path | Question | Pass Condition |
| --- | --- | --- |
| Old producer -> new consumer | Can new consumers read old requests/events/data/config? | default/upcaster/dual-read handles old shape |
| New producer -> old consumer | Can old consumers read new responses/events/data/config? | additive-only, bridge, or old path still served |
| Old code -> new data | Can rollback read data written by new code? | old reader ignores or bridge writes old representation |
| Delayed consumer -> retained events | Can lagging consumers process retained messages? | schema compatibility covers retention/replay window |
| Generated client -> provider | Do generated clients preserve source/binary compatibility? | generated diff and compile tests pass or major version is used |

## Mitigation Pattern Matrix

| Pattern | Use When | Controls |
| --- | --- | --- |
| Additive optional change | Existing semantics do not change | unknown-field tolerance, docs, tests |
| Bridge/alias | Rename or semantic migration needs old/new names | accept/read both, write both or map, precedence, telemetry |
| Expand/migrate/contract | Cleanup cannot be atomic | separate phases, migration telemetry, cleanup gate |
| Versioned endpoint/schema | Existing semantics must break | version, migration guide, deprecation window, old support |
| Upcaster/adapter | Old events/data need transformation | version tag, deterministic mapping, replay tests |
| Feature flag/opt-in | Behavior can be isolated by client/tenant | default old behavior, rollback flag, telemetry |
| Dual publish/write | Consumers migrate across event/store/field | duplicate handling, reconciliation, removal gate |
| Config bridge | Config key/default changes during rolling restart | old/new key support, precedence, cleanup owner |

## Anti-Patterns

- "No callers" based only on local `rg`.
- Server unit tests presented as consumer compatibility proof.
- Generated clients changed without semver, public API diff, compile, or downstream smoke.
- Event payload changed without replay fixture, schema registry mode, or subscriber inventory.
- Deprecation removed because a date elapsed while telemetry still shows usage.
- Rollback defined as redeploying old code without checking new data/events/config.
