# Compatibility Benchmarks

Load this reference only when public API, SDK, schema, or multi-version rollout compatibility is under review.

## Benchmark Anchors

Anchor against: **Semantic Versioning (semver.org)** - MAJOR.MINOR.PATCH; breaking change increments MAJOR; consumer pinning strategies. **Postel's Law (Robustness Principle, RFC 793)** - "be conservative in what you send, liberal in what you accept" - relevant to forward compatibility design. **Google API Improvement Proposals (AIP-180)** - compatibility policy; what constitutes breaking vs. non-breaking; major version in URL path. **Expand-Contract (Parallel Change) - Martin Fowler** - the safest database/API migration pattern for rolling deployments. **Apache Avro / Confluent Schema Registry** - schema evolution rules (BACKWARD, FORWARD, FULL compatibility modes); schema registry enforcement before event publication. **gRPC Protocol Buffer compatibility rules** - field number stability; reserved fields; unknown field handling. **OpenAPI Specification (OAS) versioning** - semver in `info.version`; vendor extensions for deprecation annotations; overlay specs for client code generation stability. **Netflix API Evolution** - versioning strategy for long-lived mobile clients; sunset header (RFC 8594) for graceful API retirement. **RFC 8594 (Sunset Header)** - machine-readable deprecation date in HTTP response headers. **DORA Deployment Frequency / Change Failure Rate** - rollback safety as a DORA metric; expand-contract enables high-frequency deployment with zero-downtime migrations.

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
