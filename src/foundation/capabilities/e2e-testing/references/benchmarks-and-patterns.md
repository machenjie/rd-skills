# E2E Journey Selection Patterns

These patterns compare assembled-journey proof with lower-level evidence and remaining risk.

## Admit A Journey

Use assembled-system proof when the material failure requires several deployed boundaries to operate together or current policy names the journey. Record the lower-level evidence considered and the remaining risk it cannot close.

| Journey facet | Easy-to-miss failure | Proof focus |
| --- | --- | --- |
| Identity and permission | cached role, tenant mix-up, session expiry, object-level denial | allowed and denied outcomes plus non-leak behavior |
| Durable state | UI success precedes commit, rollback, queue, or audit failure | visible result plus authoritative state and forbidden effects |
| Eventual result | fixed sleep passes too early or times out nondeterministically | semantic readiness and bounded observation derived from system behavior |
| External sandbox | uncontrolled cost, rate, stale fixture, or unsafe side effect | owned sandbox scope or contract-backed substitute with explicit limits |
| Version coexistence | route, client, schema, or persisted state differs across versions | risk-selected old/new combinations and recovery path |

## Isolation And Cleanup Pattern

1. Allocate a run-owned identity, tenant, record, namespace, or correlation key.
2. Make setup observable and fail before the journey if preconditions are not established.
3. Clean up on success, assertion failure, timeout, and cancellation; preserve diagnostics without preserving unsafe state.
4. Verify cleanup cannot delete another run's data and disclose state that requires manual ownership.

## Flake Triage

- Classify the signature as product race, readiness error, fixture collision, environment drift, selector coupling, or resource pressure before rerunning.
- Use a rerun to collect comparison evidence, not to replace the failed result.
- Quarantine only with an owner, release consequence, diagnostic signature, and condition for repair, replacement, or removal.
- Select browsers, devices, environments, and versions from affected usage and support policy, with uncovered combinations stated explicitly.
