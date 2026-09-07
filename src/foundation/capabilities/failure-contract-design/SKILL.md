---
name: failure-contract-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when retryable, terminal, timeout, partial-failure, or fallback semantics change across boundaries; skip unchanged failures."
---

# failure-contract-design

## Registry Trigger

**Use when**

- failure meaning taxonomy retryable terminal timeout cancellation dependency partial degraded boundary translation safe representation cause preservation

**Do not use when**

- no task-local failure contract design decision is required

## Skill Role

Define typed failure meaning, boundary translation, partial/degraded ownership, authorized cause, and safe representation. Exclude retry mechanics and queue disposition.

## High-Value Rules

- Separate typed consumer meaning from authorized cause at each changed boundary.
- Own partial/degraded meaning and recovery.
- Load only the named Reference for active selection, closure, or proof.

## Anti-Patterns

- Local success substituted for evidence of the failure contract design contract.

## Stop Conditions

- Route retry identity/budgets and unknown outcomes to `idempotency-retry-design`; queue disposition to `message-queue-design`.
- Route effect recovery to `transaction-consistency` or `data-side-effect-flow-tracing`; operational diagnostics to `logging-error-handling`, `observability`, or `reliability-observability-gate`.
- Route public failure contracts to `error-code-design` and `data-api-contract-changer`; disclosures to `security-privacy-gate`.

## Output Contract

- Failure Contract with stable taxonomy, boundary translation, retryable or terminal meaning, partial or degraded outcomes, safe external and internal representations, preserved cause, negative-path evidence, specialist routes, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Failure taxonomy, translation, retry, or degraded-state semantics need selection | No material boundary or failure behavior changes | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Failures span partial outcomes, cancellation, dependencies, or async terminal states | One internal error remains fully contained | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Failure claims need fresh translation, redaction, and recovery tests | No safety or retryability claim is being closed | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
