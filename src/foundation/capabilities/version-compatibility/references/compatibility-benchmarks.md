# Compatibility Benchmarks

Load this reference when public API, SDK, schema, event, config, stored-data, generated-client, or multi-version rollout compatibility is under review.

## Benchmark Anchors

Anchor against: **Semantic Versioning (semver.org)** - MAJOR.MINOR.PATCH; breaking change increments MAJOR; consumer pinning strategies. **Postel's Law (Robustness Principle, RFC 793)** - "be conservative in what you send, liberal in what you accept" - relevant to forward compatibility design. **Google API Improvement Proposals (AIP-180)** - compatibility policy; what constitutes breaking vs. non-breaking; major version in URL path. **Expand-Contract (Parallel Change) - Martin Fowler** - the safest database/API migration pattern for rolling deployments. **Apache Avro / Confluent Schema Registry** - schema evolution rules (BACKWARD, FORWARD, FULL compatibility modes); schema registry enforcement before event publication. **gRPC Protocol Buffer compatibility rules** - field number stability; reserved fields; unknown field handling. **OpenAPI Specification (OAS) versioning** - semver in `info.version`; vendor extensions for deprecation annotations; overlay specs for client code generation stability. **Netflix API Evolution** - versioning strategy for long-lived mobile clients; sunset header (RFC 8594) for graceful API retirement. **RFC 8594 (Sunset Header)** - machine-readable deprecation date in HTTP response headers. **DORA Deployment Frequency / Change Failure Rate** - rollback safety as a DORA metric; expand-contract enables high-frequency deployment with zero-downtime migrations.

## Contract Surface Inventory Matrix

| Surface | Compatibility question | Evidence to require |
| --- | --- | --- |
| REST/HTTP API | Can old and new clients parse request, response, error, pagination, rate-limit, and auth semantics? | OpenAPI diff, generated client diff, contract tests, error examples. |
| gRPC/Protobuf | Are field numbers stable, removed fields reserved, and unknown fields tolerated? | `buf breaking`, proto diff, generated client compile. |
| Event stream/message schema | Can old and new producers/consumers deserialize and interpret payloads over retention/replay windows? | Schema registry mode, AsyncAPI/schema diff, replay fixture, consumer inventory. |
| Webhook/provider integration | Can external parties handle payload, signature, retry, version, and timeout changes? | Provider spec/captured sandbox response, partner notification, contract fixture. |
| Stored data/schema version | Can old and new code read data written by the other version? | Reader/writer matrix, expand/migrate/contract plan, rollback query. |
| Config/environment | Can old and new binaries read old and new config names/defaults during rolling restart? | Old/new key bridge, precedence rule, restart matrix, config telemetry. |
| SDK/package/public export | Does semver match source/binary API compatibility and generated artifacts? | Public API diff, semver decision, downstream compile/test, changelog. |
| CLI output/scripted interface | Do scripts depending on fields, status codes, stdout/stderr, or exit codes keep working? | Golden fixtures, migration note, deprecation window. |
| Mobile/partner/public clients | Does the compatibility window cover clients that cannot be force-upgraded? | Supported version telemetry, partner schedule, Sunset/Deprecation signal. |

## Breaking Change Classification Matrix

| Change Type | Backward Compatible? | Forward Compatible? | Breaking? | Required Mitigation |
| --- | --- | --- | --- | --- |
| Add optional field to response | Yes (clients ignore it) | Yes | No | None |
| Add optional field to request | Yes | Yes | No | None |
| Add required field to request | No | No | **Yes** | Default value in transition; or versioning |
| Remove field from response | No | No | **Yes** | Expand-contract; deprecation window |
| Remove field from request | Yes (ignored if optional) | No | Potentially | Verify no consumer sends it |
| Rename field | No | No | **Yes** | Expand-contract (old + new both accepted) |
| Change field meaning/semantics | No | No | **Yes** | Versioning required |
| Tighten validation rule | No | No | **Yes** | Versioning or communication to all producers |
| Add new enum value in response | No (old code may not handle) | Yes | **Yes for old code** | Defensive handling required; communication |
| Remove enum value | No | No | **Yes** | Verify no producer emits; verify no consumer expects |
| Change error code / error shape | No | No | **Yes** | Versioning or explicit mapping layer |
| Change default value | No (breaks existing behavior) | No | **Yes** | Explicit opt-in required |
| Add new event type to stream | Yes (consumers ignore) | Yes | No | None |
| Rename event type | No | No | **Yes** | Dual publish; expand-contract |
| Change config key name | No | No | **Yes** | Both keys accepted in transition window |

## Compatibility Dimension Matrix

| Dimension | Examples | Why schema-only review misses it | Required evidence |
| --- | --- | --- | --- |
| Structure | Field added/removed/renamed/retyped, endpoint moved, event name changed. | Machine schemas catch some but not all generated-client or parser behavior. | Schema diff, generated client compile, contract tests. |
| Meaning | `currency` now ISO code, `status` now includes moderation, `total` changes units. | Shape is unchanged while consumer calculations become wrong. | Before/after semantics, migration notes, consumer acceptance. |
| Validation | Requiredness, regex, min/max, enum set, rejection of unknown fields. | Consumers fail at runtime with 4xx or deserialization errors. | Request fixtures, backward-compatible defaults, validation diff. |
| Defaults | Timeout, page size, sort, locale, feature flag, retry count. | Existing callers omit field and behavior changes anyway. | Default map, opt-in flag, telemetry impact. |
| Error behavior | Status code, problem body, retryable flag, error code. | Success schema compatibility says nothing about failure paths. | Error contract tests and client remediation map. |
| Timing/SLA | Timeout, retry horizon, async vs sync, eventual consistency. | Contract shape remains valid but client expectations break. | SLO/timeout diff, frontend/integration behavior tests. |
| Ordering/pagination | Sort order, cursor semantics, partition key, event ordering guarantee. | Same fields arrive in different order or missing page boundaries. | Pagination/event-order fixtures and consumer tests. |
| Persistence/rollback | New code writes values old code cannot read. | API diff may pass while rollback crashes old binary. | Old/new reader-writer matrix and rollback validation. |

## Producer/Consumer And Rollback Matrix

| Direction | Question | Pass condition |
| --- | --- | --- |
| Old producer -> new consumer | Can new code read old requests/events/data/config? | New code accepts old shape/defaults or has migration/upcaster. |
| New producer -> old consumer | Can old code read new responses/events/data/config? | Additive-only, unknown fields tolerated, enum/default compatible, or old path still served. |
| Old code -> new data | If rollback happens after new writes, does old code work? | Old code ignores new fields or bridge writes old representation too. |
| New code -> old data | During canary, can new code handle old records/config/messages? | New code has defaults, backfill guard, or dual-read. |
| Delayed consumer -> retained events | Can a lagged consumer process messages produced during rollout? | Schema compatibility covers queue retention/replay window. |
| Generated client -> provider | Do compiled clients keep source/binary compatibility? | Generated client diff and compile tests pass or major version is used. |

## Mitigation Pattern Matrix

| Pattern | Use when | Required controls |
| --- | --- | --- |
| Additive optional change | New field/operation does not change existing semantics. | Unknown-field tolerance, docs, tests, no required client action. |
| Bridge/alias | Rename or semantic migration needs both old and new names. | Accept/read both, write both or map, precedence, telemetry for old usage. |
| Expand/migrate/contract | Stored data or contract cleanup cannot be atomic. | Separate deploy phases, old/new compatibility, cleanup only after telemetry. |
| Versioned endpoint/schema | Existing semantics must break. | New version, migration guide, deprecation window, old version support. |
| Upcaster/adapter | Events/data need old payloads transformed for new consumers. | Version tag, deterministic mapping, replay tests, dead-letter plan. |
| Feature flag/opt-in | Behavior change can be isolated by client or tenant. | Default old behavior, per-client enablement, rollback flag, telemetry. |
| Dual publish / dual write | Consumers migrate from old event/field/store to new. | Atomicity or reconciliation, duplicate handling, removal gate. |
| Config bridge | Key/default rename during rolling restart. | Accept old and new key, precedence rule, telemetry, cleanup date. |

## Deprecation And Telemetry Gate Matrix

| Surface | Minimum evidence before removal | Useful telemetry |
| --- | --- | --- |
| Internal API/field | Migration window agreed by owners and usage at zero or threshold. | Endpoint/field access by caller/service/version. |
| Public/partner API | Published migration guide, partner notice, support window, approval. | API key/client id/version calls to old surface. |
| Mobile API | Supported app version window and app-store adoption telemetry. | App version distribution, endpoint version calls, crash/error rate. |
| Event schema/topic | Consumer lag/replay window closed and all active consumers verified. | Consumer group schema version, DLQ/deserialization errors. |
| SDK/package export | Major version or compatibility bridge plus downstream compile evidence. | Package download/version telemetry where available. |
| Config key/default | All running instances use new key/default and old key reads are zero. | Config read counters, deployment version, restart status. |

## Rollback Safety Decision Tree

```
Before approving a release containing a migration:

1. What data does the NEW code write that the OLD code cannot read?
   NONE → Rollback-safe from data perspective
   SOME → Rollback will produce errors or corrupt state
          → MUST redesign: add expand phase before data writes change

2. What behavior does the NEW code expose that existing consumers depend on changing?
   NONE → Safe to rollback
   SOME → Existing consumers will break after rollback
          → MUST deploy backward-compatible bridge before removing old behavior

3. Can the migration be run BEFORE the code deployment (expand phase)?
   YES → Run migration first; deploy code second; verify; THEN run contract phase
   NO  → Cannot be deployed with zero-downtime; must schedule maintenance window

4. If we rollback, will the last 24h of written data be readable by old code?
   YES → Rollback-safe
   NO  → Add rollback data migration script BEFORE shipping; test it
```

## Graph, Memory, And Execution Coupling

| Evidence source | How to use it | Failure to avoid |
| --- | --- | --- |
| Repository graph | Search providers, consumers, generated clients, schemas, topics, configs, migrations, packages, docs, tests, dashboards, and jobs. | Treating service source only as full consumer inventory. |
| Project memory | Use prior compatibility decisions as leads. Confirm the contract, consumer list, and deprecation policy still exist. | Copying stale "internal only" or "safe enum" claims. |
| Execution trajectory | Reuse prior validation only if it covers the changed surface and current generated artifacts. | Claiming old contract tests prove a new schema. |
| Telemetry | Measure old/new surface usage before cleanup. | Calendar-only deprecation or assuming docs migrated users. |
| Generated artifacts | Compare generated SDK/client/public export changes. | Server tests pass while clients fail to compile. |

## Compatibility-To-Validation Matrix

| Compatibility decision | Preferred validation |
| --- | --- |
| API request/response shape | OpenAPI diff, Pact/provider verification, generated client compile, success and error fixture tests. |
| DTO field nullability/default | Schema diff plus old/new fixture replay including absent/null/default cases. |
| Error code/body change | Contract tests for each status and client remediation behavior. |
| Enum/status expansion | Unknown-value handling test or generated-client compile plus migration notice. |
| Event schema evolution | Schema registry compatibility check, AsyncAPI/proto diff, replay fixture, consumer verification. |
| Stored data compatibility | Old/new reader-writer test, migration validation query, rollback rehearsal. |
| Config key/default bridge | Old/new binary and old/new config matrix test; telemetry for old key reads. |
| SDK/package export | Public API diff, semver decision, downstream compile/test, changelog. |
| Deprecation removal | Usage telemetry below threshold, window elapsed, owner approval, docs/migration guide. |
| Mixed-version rollout | Canary or staged deployment plan with rollback flag, bridge, and validation checkpoint. |

## Review Checklist

1. Name every affected contract surface.
2. Separate structure, meaning, validation, defaults, timing, ordering, error, and persistence compatibility.
3. Inventory known consumers and document unknown-consumer risk.
4. Check generated clients, SDKs, public exports, mobile versions, partner integrations, events, jobs, dashboards, and scripts.
5. Build old/new producer-consumer and old/new data-reader matrices.
6. Choose additive, bridge, versioning, upcaster, feature flag, dual-write, or expand/migrate/contract strategy.
7. Define mixed-version behavior and immediate rollback state.
8. Require telemetry gate before removal.
9. Require contract/schema/generated-client/fixture validation or record residual risk.
10. Name handoffs and evidence limits before approval.

## Anti-Pattern Review

| Anti-pattern | Review response |
| --- | --- |
| "Only internal callers" | Require service, job, dashboard, event, generated-client, and telemetry search. |
| "Optional field is always safe" | Check closed schemas, generated clients, semantic changes, and strict consumers. |
| "Add enum value is non-breaking" | Check exhaustive switches, generated SDKs, old app versions, and event consumers. |
| "Remove after 30 days because docs said so" | Require telemetry zero-use and owner approval. |
| "Rollback is redeploy old version" | Verify old version can read data/config/events written by new version. |
| "Contract tests pass for 200 response" | Require error/null/optional/enum/pagination cases if consumers depend on them. |
| "Config rename is simple" | Require old/new key bridge across rolling restarts. |
| "Schema registry default is enough" | Set and verify BACKWARD/FORWARD/FULL based on producer/consumer needs. |
