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
| Unit | No local rule changed, or another selected level already proves the same material rule and failure mechanism. | A changed local rule has an unproved outcome that an isolated test can expose reliably. |
| Integration | No real boundary changed, or selected proof already exercises its material semantics; relevant doubles remain contract-aligned. | A material storage, queue, provider, transaction, serialization, timeout, or retry interaction remains unproved without the real boundary. |
| Contract | No consumer-visible contract changed, or equivalent selected consumer/provider proof closes it. | A changed producer/consumer obligation has a compatibility or semantic failure not exposed by selected proof. |
| E2E | Lower levels close the material journey risks and no distinct assembled-orchestration mechanism remains unproved. | An assembled journey has a material routing, session, effect, or recovery failure that selected lower-level proof cannot expose. |
| Migration/rollback | No recovery or coexistence behavior changed, or selected evidence already exercises its material state transitions. | A changed migration, coexistence, cleanup, restore, or asymmetric recovery mechanism remains unproved. |
| Security/performance | No relevant boundary or resource behavior changed, or selected proof closes the reachable risk. | A reachable authority, sensitive-data, or resource failure needs a distinct adversarial, load, or measurement oracle absent from selected proof. |
