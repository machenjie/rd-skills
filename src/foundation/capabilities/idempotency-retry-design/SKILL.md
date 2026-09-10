---
name: idempotency-retry-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when retries, idempotency, deduplication, timeout, or replay safety affects side effects; skip when operations cannot repeat."
---

# idempotency-retry-design

## Registry Trigger

**Use when**

- design idempotency keys retries backoff deduplication and replay safety

**Do not use when**

- no task-local idempotency retry design decision is required

## Skill Role

Define operation identity, record/effect coordination, unknown outcomes, late replay, retry budgets, and terminal resolution. Exclude transaction, provider, and queue design.

## High-Value Rules

- Bind business identity to record/effect coordination and concurrent state.
- Define unknown outcomes, replay horizon, aggregate retry budget, and owned terminal resolution.
- Select the named Reference for multi-boundary closure, proof, or competing mechanisms.
- When the selected idempotency or retry decision remains active, load only its named Reference.

## Anti-Patterns

- Do not infer identity, effect status, or replay safety from a transport key, timeout, or one retry layer.

## Stop Conditions

Escalate ambiguous identity, uncoordinated record/effect, unresolved unknown outcomes, protection shorter than replay, unproved tenant/principal binding, or unowned terminal work involving money, permissions, inventory, legal records, or irreversible effects.

## Output Contract

- operation identity and retry contract with record/effect coordination, crash boundaries, concurrent states, unknown and late replay behavior, aggregate budget, and owned terminal resolution

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Concurrency crash windows retention replay or terminal ownership spans multiple boundaries | Root rules resolve one bounded repeat path without cross-boundary crash late-replay or terminal ambiguity | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Duplicate safety unknown outcome isolation recovery or terminal-resolution claims need fresh proof | No replay-safety isolation recovery or terminal-resolution claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [industry benchmarks](references/industry-benchmarks.md) | benchmark-pattern | Competing identity coordination retry or late-replay patterns remain viable | Current operation and authority evidence determine one safe pattern | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
