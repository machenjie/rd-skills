# Testability Seam Checklist

Use this checklist when a change proposes a seam, test double, fixture, deterministic source, or public behavior boundary. Keep answers concrete and tied to current source.

- Name the public behavior boundary and the observable output, state change, event, or side effect under test.
- State the private-helper non-export decision and the rejected visibility widening path.
- For the scoped observable behavior, inventory reachable collaborators, external IO, clocks, randomness, UUIDs, environment, schedulers, feature flags, fixtures, generated inputs, and dependency-graph overrides. The inventory records externally owned or deliberately real boundaries instead of instantiating unrelated seam types.
- When choosing a fake, stub, mock, spy, or real boundary, name the concrete risk it exposes and the relevant provider behavior it cannot represent. A mechanism unable to fail for that risk is not closure evidence.
- Prove double fidelity with contract, integration, calibration, or limitation evidence when the double represents a real provider.
- Define deterministic controls for time, randomness, UUIDs, locale/timezone, concurrency, async scheduling, environment, filesystem, network, DB, cache, and queue behavior.
- Consume the accepted `test-data-management` owner for fixtures, builders, seeds, snapshots, goldens, namespaces, privacy, and asynchronous cleanup.
- Define only the seam-specific reset and observation obligations needed to honor that decision.
- Characterize current public behavior before risky refactor, extraction, split, merge, or dependency inversion.
- Reject snapshot-only, golden-update-only, private-call-order-only, sleep/retry-only, and test-only-interface shortcuts unless residual risk is explicitly accepted.
- Map repository inspection edges, accepted/rejected prior claims, execution order, validation command, report path, exit code, and stale/not-run scope before closure.
