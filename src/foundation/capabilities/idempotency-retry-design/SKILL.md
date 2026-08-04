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

- **Define business identity before choosing a key mechanism.** Bind principal, tenant, subject, operation, canonical request meaning, and version or canonicalization effects into identity matching.
- **Coordinate the idempotency record with the business side effect.** Map crash windows around acceptance, effect commit, result persistence, publication, and acknowledgement.
- Choose a mechanism that closes every reachable duplicate-or-loss window.
- **Specify same-identity concurrency as a state contract.** Define pending, succeeded, failed, and unknown ownership and responses so concurrent arrivals cannot cause duplicate or conflicting business effects or mistake in-flight work for completion.
- **Treat timeout, cancellation, and transport loss as unknown until commit status is proven.** Reconcile with the authoritative effect before replay unless repeat safety is proven; reuse an established result when it exists.
- **Derive retention and late-replay behavior from reachable replay sources.** Cover clients, brokers, providers, workflows, backfills, and disaster recovery; define what an expired identity or tombstone permits, rejects, or reconciles.
- **Bound the aggregate retry budget across layers.** Account for callers, libraries, gateways, queues, schedulers, and workers together; prevent amplification and define cancellation, pacing, recovery, and downstream-load limits from current semantics.
- **End exhausted or permanent failure in an owned observable state.** Name the authority for reconciliation, compensation, manual recovery, or accepted loss; silent discard and endless retry are invalid terminal behavior.

## Anti-Patterns

- Treat a transport key, request attempt, or caller-generated token as business identity without proving scope, canonical meaning, collision behavior, and authorization.
- Use check-then-act coordination or infer success or failure from a timeout while record/effect ordering and authoritative status remain unknown.
- Optimize one retrying layer while ignoring aggregate amplification, late replay, terminal ownership, or cross-tenant result exposure.

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
