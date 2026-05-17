# Degradation Circuit Breaking Checklist

- Identify dependency, protected core flow, and failure modes.
- Define timeout, bounded retry, fallback, and terminal failure behavior.
- Decide fail-open, fail-closed, queued, stale, skipped, or degraded response.
- Set circuit breaker thresholds, open behavior, half-open recovery, and owner.
- Add bulkhead, rate limit, or isolation when dependency failure can exhaust shared capacity.
- Observe fallback usage, circuit state, dependency health, and user impact.
