# Test Strategy Checklist

- **Model negative and nondeterministic outcomes.** Include reachable denial, invalid input, conflict, timeout, rollback, retry, partial failure, and duplicate effects. For concurrency or eventual consistency, assert allowed terminal results and forbidden states with bounded observable waits rather than one scheduler interleaving.
- Identify change type, impacted surfaces, risk level, and failure consequence.
- Map each risk to the cheapest reliable test level that can prove it.
- Add another test level only when it exercises a distinct material mechanism, boundary, consumer, or oracle.
- Treat a risk label alone as insufficient evidence for layered tests.
- Include negative, permission, failure, rollback, migration, and regression paths where affected.
- For concurrent or nondeterministic behavior, assert that each observed outcome belongs to the allowed terminal-result set. Also assert explicit forbidden states and side effects without requiring one scheduler interleaving when several are correct.
- Record omitted test levels with rationale, residual risk, and compensating evidence.
- Treat flaky-test retry or quarantine as diagnostic containment, not passing evidence.
- Preserve the first failure, reproduction inputs, and available logs or artifacts.
- Require a named owner, remediation condition, and fresh evidence of the original failure mechanism before counting the test as passing.
- Trace recommended test evidence back to acceptance criteria.
- Route validation coverage and admissibility judgment to `quality-test-gate`.
- Send release-relevant evidence gaps to `delivery-release-gate` without issuing a release verdict.

## Omission Review Pattern

| Omitted level | Accept when | Reject when |
| --- | --- | --- |
| Unit | Pure wiring has no local rule and boundary proof fails for the same risk. | Logic, permission, calculation, mapping, or state changed. |
| Integration | No real boundary changed and doubles are contract-aligned. | Storage, queue, provider, transaction, serialization, timeout, or retry semantics matter. |
| Contract | No public API/event/SDK/schema/export consumer can observe the change. | Shape, error, generated client, event, or export changed. |
| E2E | Lower levels prove behavior and no critical journey orchestration changed. | Journey, routing, session, payment, download, or destructive action changed. |
| Migration/rollback | No data shape, coexistence, backfill, cleanup, restore, or rollback state changed. | Data/schema changed or rollback is asymmetric. |
| Security/performance | No trust boundary or resource-sensitive path changed. | Security or resource-sensitive behavior can regress. |
