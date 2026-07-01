# Testability Seam Checklist

Use this checklist when a change proposes a seam, test double, fixture, deterministic source, or public behavior boundary. Keep answers concrete and tied to current source.

- Name the public behavior boundary and the observable output, state change, event, or side effect under test.
- State the private-helper non-export decision and the rejected visibility widening path.
- Identify every seam: collaborator, external IO, clock, random, UUID, environment, scheduler, feature flag, fixture, generated input, or dependency graph override.
- Choose fake, stub, mock, spy, or real-boundary verification by the risk the test must catch.
- Prove double fidelity with contract, integration, calibration, or limitation evidence when the double represents a real provider.
- Define deterministic controls for time, randomness, UUIDs, locale/timezone, concurrency, async scheduling, environment, filesystem, network, DB, cache, and queue behavior.
- Assign fixture, builder, seed, snapshot, and golden ownership with fields asserted, update/delete path, and privacy boundary.
- Characterize current public behavior before risky refactor, extraction, split, merge, or dependency inversion.
- Reject snapshot-only, golden-update-only, private-call-order-only, sleep/retry-only, and test-only-interface shortcuts unless residual risk is explicitly accepted.
- Map repository graph edges, accepted/rejected memory claims, execution order, validation command, report path, exit code, and stale/not-run scope before closure.
