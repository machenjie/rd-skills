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

Define stable failure meaning through typed classification, boundary translation, retryable or terminal outcomes, partial or degraded results, cause preservation, and safe representations. Exclude retry mechanics and queue disposition.

## High-Value Rules

- Define a machine-distinguishable failure contract at each changed material boundary; message text alone is not a stable contract.
- Classify validation, permission, conflict, timeout, cancellation, dependency, partial, degraded, internal, retryable, and terminal outcomes only when the distinction changes a caller decision, disclosure, or owner.
- Keep timeout, cancellation, unknown write outcome, and terminal rejection distinct; this Skill classifies their meaning but routes retry identity, deduplication, budgets, and backoff to the retry specialist.
- Translate framework, provider, repository, and storage failures at the boundary that owns the abstraction while preserving the authorized diagnostic cause.
- Represent partial and degraded outcomes explicitly so callers can distinguish completed effects, unavailable data, stale data, and work that still needs specialist-owned recovery.
- Separate stable safe user or consumer meaning from internal cause and correlation evidence without exposing secrets, protected existence, provider payloads, SQL, paths, prompts, or tool output.
- Treat repository inspection, generated contracts, and prior task evidence as leads; current negative paths and boundary tests determine which failure claims are verified.

## Anti-Patterns

- Returning `null`, empty success, or a generic fallback after a failure hides degraded or terminal meaning and loses the cause.
- Collapsing every failure into one internal category makes caller recovery, disclosure, and ownership indistinguishable.
- Passing raw provider, SDK, database, ORM, or storage errors across an adapter or repository boundary leaks unstable internals and couples consumers to dependency wording.
- Marking an unknown write outcome retryable before the retry specialist proves identity and reconciliation can duplicate durable effects.
- Reporting a partial result as total success or generic failure hides which effects escaped and who owns the remaining outcome.
- Treating cancellation as failure can resurrect caller-abandoned work or create false operational noise.

## Stop Conditions

- Route idempotency keys, deduplication, replay, backoff, retry budgets, and unknown-outcome reconciliation to `idempotency-retry-design`.
- Route acknowledgement, retry exhaustion, poison messages, terminal queue disposition, and replay mechanics to `message-queue-design`.
- Route effect ordering, compensation, reconciliation, and transaction ownership to `transaction-consistency` or `data-side-effect-flow-tracing`.
- Route log fields, metrics, traces, alerts, dashboards, fallback operations, and incident response to `logging-error-handling`, `observability`, or `reliability-observability-gate`.
- Route public status, error codes, SDK behavior, event/webhook compatibility, or localization to `error-code-design` and `data-api-contract-changer`.
- Escalate to `security-privacy-gate` when any external or diagnostic representation can disclose secrets, PII, authorization state, tenant or resource existence, provider internals, SQL, paths, prompts, or tool output.

## Output Contract

- Failure Contract with stable taxonomy, boundary translation, retryable or terminal meaning, partial or degraded outcomes, safe external and internal representations, preserved cause, negative-path evidence, specialist routes, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Failure taxonomy, translation, retry, or degraded-state semantics need selection | No material boundary or failure behavior changes | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Failures span partial outcomes, cancellation, dependencies, or async terminal states | One internal error remains fully contained | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Failure claims need fresh translation, redaction, and recovery tests | No safety or retryability claim is being closed | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
