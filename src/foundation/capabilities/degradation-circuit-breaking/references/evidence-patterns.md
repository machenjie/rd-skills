# Degradation Circuit Breaking Evidence Patterns

Use this reference when degradation closure depends on validation freshness, prior source or task evidence claims, execution output, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second resilience pattern catalog.

## Degradation-To-Validation Map

| Degradation claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Dependency criticality is correct | Current caller path, dependency owner, protected flow, fail-open or fail-closed decision, and product/security approval when needed | The inspected dependency is classified for the named flow | All tenants, future callers, or uninspected fallback paths share the same criticality |
| Dependency phase timeouts stay beneath immutable ceilings | Gateway-owned end-to-end and hop-deadline ceilings, or documented out-of-chain local ceilings; downstream connection/read/phase timeouts; cancellation path; and timeout test or review artifact | The inspected timeout policy consumes rather than redefines its applicable ceilings | The gateway ceilings are correctly selected, provider latency distribution is stable, or production pool saturation is safe |
| Actual retry policy stays beneath retry and deadline ceilings | Gateway-owned or documented local retry/deadline ceilings, retryable/non-retryable list, max attempts, jitter/backoff, idempotency proof, unknown-outcome handling, and retry-load estimate | The inspected operation's concrete policy avoids obvious duplicate effects, ceiling violations, and retry storms | All provider edge cases or cross-service fan-out behavior is covered |
| Circuit breaker is calibrated | Failure window, minimum volume, open duration, half-open probe, close threshold, and state metric evidence | The inspected circuit has explicit thresholds and observable state | Thresholds are optimal for future traffic shifts |
| Fallback is distinguishable from correctness | Typed degraded response, user impact, stale-data ceiling, approval owner, and fallback test | The inspected fallback does not silently masquerade as normal behavior | Every downstream consumer handles degraded state correctly |
| Bulkhead or load shedding contains blast radius | Pool/queue/concurrency bound, reject behavior, saturation metric, and fault or load evidence | The inspected dependency cannot consume unbounded shared resources | Production scheduler behavior or all workload mixes are proven |
| Recovery evidence is fresh | Current test, chaos drill, dashboard, report, or manual artifact with timestamp and final-source freshness | The named evidence still covers the edited degradation decision | Live provider recovery, all regions, or future config edits remain covered |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old incidents, dashboards, and prior validation as selectors until current source and fresh validation confirm them.
- Accept prior "safe fallback", "optional dependency", "circuit already protects it", or "timeout configured" claims only when current call paths, config, telemetry, and tests still match.
- Mark evidence stale after edits to gateway-ceiling inputs, dependency calls, timeout/retry/circuit settings, fallback shape, config flags, pool boundaries, metrics, dashboards, tests, reports, or build outputs.
- For each final resilience claim about an inspected failure path, cite a command, test, report, dashboard, or owner review; otherwise record it as not run with residual risk.

- If fault injection, chaos test, load test, circuit toggle, feature flag, or kill switch change, record environment, permission, stop condition, rollback or disable path, owner, and redaction rule.
- If production telemetry query or dashboard export, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.
