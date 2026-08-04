# Integration Testing Benchmarks And Patterns

Load this reference when real persistence, cache, broker, HTTP adapter, framework, transaction, or process integration carries the change risk. Do not load it when a pure local rule or externally versioned consumer contract is the primary claim.

## Boundary And Fidelity

| Boundary | Candidate setup | Required proof and limit |
| --- | --- | --- |
| Controller/service/repository/database | Framework slice with a production-compatible disposable database or owned test instance. | Request/return, durable state, constraints/transaction, tenant/permission, and cleanup; local engine is not production scale. |
| Cache or NoSQL adapter | Real disposable service or calibrated emulator/fake. | Key/scope/TTL/invalidation/failure behavior; emulator/provider differences are named. |
| Producer/consumer/broker | Owned topic/queue/namespace with actual serialization and handler boundary. | Ack/commit order, duplicate/retry/DLQ, durable effects, cleanup, and timing limit. |
| HTTP/provider adapter | Contract-calibrated stub/sandbox with request verification. | Method/path/auth/body/error/timeout mapping; stub does not prove provider deployment. |
| Transaction/outbox | Real commit boundaries plus injected failure. | No partial state, publish-after-commit/durable handoff, duplicate recovery, and separate-transaction awareness. |
| Auth enforcement | Real middleware/filter/principal and resource query path. | Allowed and wrong-role/owner/tenant cases with no state/data leak. |

Apply the accepted `test-data-management` decision for rollback, truncation, schemas, keys, topics, queues, and data cleanup. Integration testing may select disposable seam infrastructure outside test-data scope. Verify broad flush/drop/purge only with positive ownership evidence for this run.

## Failure And Freshness

Assert the caller response, durable state, and external/queued/cache effects that belong to the boundary. Inject applicable constraint failure, exception after an early write, timeout/unknown outcome, duplicate delivery, retry/terminal handling, cache loss, auth denial, and cleanup failure. Wait on observable readiness/state with a bounded deadline rather than fixed sleeps.

Record dependency image/emulator/stub and schema/migration version, fixture owner/freshness/redaction, namespace/cleanup, environment requirements, final command/exit, and material edits after the run. Use repository-supported changed-module selection only when its dependency map is trusted; otherwise disclose what the narrow suite omits.

Integration evidence does not prove a full user journey, production capacity/distribution, managed-service/IAM configuration, every external-provider behavior, or compatibility with unknown consumers. Transaction rollback may hide separate transactions and async effects; an emulator may omit consistency, limits, or failure modes.

Reject shared mutable infrastructure, sleeps as synchronization, stale recorded payloads, rollback-only isolation for independently committed work, positive-only auth tests, container success reported as production proof, and stubs that are not contract-calibrated.

Route local rules to `unit-testing`, wire compatibility to `contract-testing`, full journeys to `e2e-testing`, data/cleanup ownership to `test-data-management`, provider risk to `integration-change-builder`, and final layer/freshness sufficiency to `quality-test-gate`.
