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
| Calculation, validation, mapping, state | Unit/property with edge and negative cases. | Use mutation/property where it challenges a consequential assertion; reject selected E2E proof only when it misses the local mechanism or oracle. |
| Orchestration with ports/adapters | Component/integration with realistic contracts. | Real store/provider when adapter behavior matters; reject mock-call-only. |
| API/event/SDK/export | Contract/schema/generated-client/compatibility fixture. | Use the supported consumer/version matrix; reject handler-only proof when it leaves a material consumer obligation unproved. |
| Migration/backfill/destruction | Forward, rollback, integrity with representative shape. | Volume and recovery handoff; reject empty-schema-only. |
| Frontend behavior | Component/route via accessibility and user behavior. | Critical journey smoke; reject CSS/snapshot-only. |
| Provider/queue/file/email | Contract/sandbox plus failure simulation. | Retry, idempotency, DLQ, reconciliation, cleanup; reject impossible mocks. |
| Security/payment/tenant/export | Denied/invalid/abuse matrix and specialist evidence. | Threat/adversarial proof; reject allowed-role happy path. |
| Performance/SLO | Representative benchmark/load/stress tied to the actual threshold. | Preserve correctness and measurement limits; reject intuition. |
| Concurrency correctness | Controlled overlap and allowed/forbidden terminal-state assertions. | Use race/idempotency/soak evidence as needed; require performance thresholds only for an actual resource claim. |

## Assertion And Omission Guardrails

- Prefer public behavior over private calls, mock counts, snapshots, or existence.
- Name the mechanism and make the assertion fail for its relevant removal/inversion/omission/order/error-swallow mutation; record fake, mock, snapshot, manual, and unproved limits.
- Reject generic “add tests” and coverage percentage as behavior proof.
- Reject an E2E, unit, or migration substitute when its inputs, boundary, or assertions miss a material matrix case, consumer obligation, or state transition.
- Add a level only for a distinct material mechanism, boundary, consumer, or oracle.
