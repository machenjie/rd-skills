# Test Strategy Checklist

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
