# Degradation Circuit Breaking Checklist

- Select mode: fail-closed, graceful degradation, latency budget, retry/circuit, bulkhead/load shedding, or repair/drill.
- Inspect current source, dependency graph, project memory, execution trajectory, SLOs, telemetry, tests, and validation freshness.
- Identify dependency, protected core flow, criticality, and failure modes.
- Define timeout, bounded retry, fallback, typed degraded response, and terminal failure behavior.
- Decide fail-open, fail-closed, queued, stale, skipped, or degraded response with product/security justification.
- Set circuit breaker thresholds, open behavior, half-open recovery, close threshold, owner, and state metrics.
- Add bulkhead, rate limit, load shedding, or isolation when dependency failure can exhaust shared capacity.
- Validate config, feature flag, provider mode, or kill-switch defaults, owner, rollback, and cleanup.
- Observe fallback usage, circuit state, timeout/retry counts, dependency health, and user impact.
- Map every timeout, retry, circuit, bulkhead, fallback, degraded response, config, metric, and chaos/test decision to validation evidence or residual risk.
