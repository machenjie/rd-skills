# Test Strategy Benchmarks And Patterns

Use this Reference for a named layer, omission, affected-test, assertion, or proof-portfolio decision; skip one obvious low-risk command.

## Benchmark Anchors

- Pyramid/test-size evidence favors local deterministic logic, fewer medium boundary/store tests, and large E2E only for critical journeys.
- Trophy evidence favors integration when behavior crosses components or services.
- Consumer-driven contracts cover API, event, SDK, and generated-client shape.
- Mutation/fault seeding must make the relevant assertion fail when its mechanism is removed, inverted, mis-mapped, or swallowed.
- OWASP evidence requires negative authorization, input, session, and abuse cases.
- DORA evidence binds release gates to consequence and rollback/recovery.

## Layer Selection Matrix

| Risk | Primary proof | Add / reject substitute |
| --- | --- | --- |
| Calculation, validation, mapping, state | Unit/property with edge and negative cases. | Mutation/property for critical money/permission; reject E2E-only. |
| Orchestration with ports/adapters | Component/integration with realistic contracts. | Real store/provider when adapter behavior matters; reject mock-call-only. |
| API/event/SDK/export | Contract/schema/generated-client/compatibility fixture. | Consumer/version matrix; reject unit-only handler. |
| Migration/backfill/destruction | Forward, rollback, integrity with representative shape. | Volume and recovery handoff; reject empty-schema-only. |
| Frontend behavior | Component/route via accessibility and user behavior. | Critical journey smoke; reject CSS/snapshot-only. |
| Provider/queue/file/email | Contract/sandbox plus failure simulation. | Retry, idempotency, DLQ, reconciliation, cleanup; reject impossible mocks. |
| Security/payment/tenant/export | Denied/invalid/abuse matrix and specialist evidence. | Threat/adversarial proof; reject allowed-role happy path. |
| Performance/concurrency/SLO | Benchmark/load/stress tied to threshold. | Race/idempotency/soak for shared state; reject intuition. |

## Assertion And Omission Guardrails

- Prefer public behavior over private calls, mock counts, snapshots, or existence.
- Name the mechanism and make the assertion fail for its relevant removal/inversion/omission/order/error-swallow mutation; record fake, mock, snapshot, manual, and unproved limits.
- Reject generic “add tests”, one E2E for a matrix, unit-only contracts, empty-schema-only migration, and coverage percentage as behavior proof.
- Add a level only for a distinct material mechanism, boundary, consumer, or oracle.
