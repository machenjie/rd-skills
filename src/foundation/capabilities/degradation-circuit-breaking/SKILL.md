---
name: degradation-circuit-breaking
description: "`analysis-agent`/`task-agent`/`review-agent`: primary-Skill-selected for timeout, fallback, bulkhead, or circuit recovery; never task owner; skip without dependency-failure impact."
---

# degradation-circuit-breaking

## Registry Trigger

**Use when**

- design fallback degradation timeout bulkhead circuit breaker and recovery behavior

**Do not use when**

- no task-local degradation circuit breaking decision is required

## Skill Role

Consume immutable gateway-owned end-to-end, hop-deadline, and retry ceilings. Beneath them, own dependency connection, read, and phase timeouts plus the actual safe/idempotent retry policy, fallback, bulkhead, circuit, and recovery. On paths without a gateway chain, derive equivalent local caller/dependency ceilings before selecting those controls.

## High-Value Rules

- When gateway-owned end-to-end, hop-deadline, and retry ceilings apply, consume them without extending or redefining them. Without a gateway chain, derive local ceilings from the caller budget, cancellation, overhead, fan-out, and amplification risk.
- Select dependency connection, read, and other phase timeouts beneath the applicable hop ceiling from remaining budget, connection/response distributions, queueing, cleanup, fan-out, and cancellation behavior.
- Define the actual retryable and non-retryable classes, maximum attempts, deadline-aware backoff and jitter, unknown-outcome handling, and amplification bound for safe or idempotent effects beneath both retry and deadline ceilings.
- Fallback and fail-open/fail-closed behavior require the product, security, or data owner whose invariant changes; record freshness and irreversible-effect limits.
- Isolate dependency resources with a bulkhead; derive breaker volume, window, open duration, probes, and close criteria from traffic and recovery.

## Anti-Patterns

- Nested timeouts can exceed the caller deadline unless budgets flow downstream.
- Prevent layered retries because they multiply dependency load.
- Add jitter when concurrent callers can synchronize retries.
- Stop further attempts while the circuit breaker is open.
- A stale or empty fallback is user-visible behavior, not a neutral implementation detail.

## Execution Checklist

1. Map dependency criticality, caller deadline, immutable gateway ceilings or out-of-chain local ceilings, resource pool, and fallback authority.
2. Record dependency connection/read/phase timeouts and the actual retry policy beneath those ceilings, plus fallback, bulkhead, breaker states, probes, and recovery criteria.
3. Verify timeout exhaustion, amplification, fallback, isolation, and half-open recovery.

## Stop Conditions

Escalate fail-open changes to authorization, fraud, compliance, payment, or irreversible effects; regulated stale data; shared-tenant blast radius; or production fault injection. Stop when an applicable gateway-owned end-to-end, hop-deadline, or retry ceiling is missing or mutable and route that decision to `network-protocol-gateway-usage`.

## Output Contract

- resilience plan with timeouts fallbacks circuit thresholds and recovery checks, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Timeout, retry, circuit, fallback, or shedding parameters remain open | No dependency failure policy or latency budget changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Failure handling spans overload, cancellation, stale fallback, or recovery | The affected path has no fallible dependency | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Resilience claims need fresh fault tests or telemetry artifacts | No fallback or recovery claim needs proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
