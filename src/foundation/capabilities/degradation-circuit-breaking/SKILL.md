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

Own bounded dependency-failure behavior under immutable gateway ceilings.

## High-Value Rules

- Consume gateway ceilings without redefining them.
- Derive local ceilings only when no gateway owns them.
- Bind phase timeouts and retry to current ceiling and failure evidence.
- Select fallback, isolation, and breaker behavior from product invariants, capacity, and recovery.
- Load only the named Reference for unresolved parameters, checks, or proof.

## Anti-Patterns

- Local success substituted for dependency-failure and recovery evidence.

## Stop Conditions

Stop when selected degradation behavior lacks an owned safety or recovery proof.

## Output Contract

- resilience plan with timeouts fallbacks circuit thresholds and recovery checks, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Timeout, retry, circuit, fallback, or shedding parameters remain open | No dependency failure policy or latency budget changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Failure handling spans overload, cancellation, stale fallback, or recovery | The affected path has no fallible dependency | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Resilience claims need fresh fault tests or telemetry artifacts | No fallback or recovery claim needs proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
