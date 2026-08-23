# Degradation Circuit Breaking Checklist

- Select mode: fail-closed, graceful degradation, latency budget, retry/circuit, bulkhead/load shedding, or repair/drill.
- Inspect current source, dependency graph, prior task evidence, observable action sequence, SLOs, telemetry, tests, and validation freshness.
- Identify dependency, protected core flow, criticality, and failure modes.
- Define timeout, bounded retry, fallback, typed degraded response, and terminal failure behavior.
- Decide fail-open, fail-closed, queued, stale, skipped, or degraded response with product/security justification.
- Set circuit breaker thresholds, open behavior, half-open recovery, close threshold, owner, and state metrics.
- Add bulkhead, rate limit, load shedding, or isolation when dependency failure can exhaust shared capacity.
- Validate config, feature flag, provider mode, or kill-switch defaults, owner, rollback, and cleanup.
- Observe fallback usage, circuit state, timeout/retry counts, dependency health, and user impact.
- Map every timeout, retry, circuit, bulkhead, fallback, degraded response, config, metric, and chaos/test decision to validation evidence or residual risk.

## Anti-Patterns

- Nested timeouts can exceed the caller deadline unless budgets flow downstream.
- Allow layered retries because they multiply dependency load.
- Skip jitter when concurrent callers can synchronize retries.
- Continue ordinary attempts while the circuit breaker is open.
- A stale or empty fallback is user-visible behavior, not a neutral implementation detail.

## Execution Checklist

1. Map dependency criticality, caller deadline, immutable gateway ceilings or out-of-chain local ceilings, resource pool, and fallback authority.
2. Record dependency connection/read/phase timeouts and the actual retry policy beneath those ceilings, plus fallback, bulkhead, breaker states, probes, and recovery criteria.
3. Verify timeout exhaustion, amplification, fallback, isolation, and half-open recovery.
