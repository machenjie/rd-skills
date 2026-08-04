---
name: domain-event-modeling
description: "`analysis-agent`/`task-agent`: use when commit timing, payloads, schema, ordering, idempotency, or retry changes; skip when no domain-event decision is required."
---

# domain-event-modeling

## Registry Trigger

**Use when**

- model domain events producers consumers payloads timing and consistency expectations

**Do not use when**

- no task-local domain event modeling decision is required

## Skill Role

Define a domain event's business meaning, authoritative producer, commit timing, subject identity, payload, compatibility, ordering, repeat delivery, consumer expectations, and evidence. Exclude broker operation and transport topology.

## High-Value Rules

- **Model a completed domain fact.** Name the past event, business meaning, subject, occurrence time, producer authority, and distinction from a command, request, snapshot, or technical notification.
- **Tie emission to the authoritative transition.** Define which state change establishes the fact, transaction or consistency boundary, publication record, and behavior when commit or publication succeeds alone.
- **Keep payload sufficient and owned.** Include stable identity, tenant or subject binding, event version, causation and correlation, and consumer-needed facts without exposing mutable internal models or unnecessary sensitive data.
- **Specify identity and ordering semantics.** Define logical event identity, duplicate behavior, subject or partition order, late and out-of-order handling, and what consumers may infer when gaps occur.
- **Design compatibility for retained and replayed facts.** Preserve meaning, unknown fields and values, defaults, schema history, old consumers, rollback readers, and deletion or redaction policy across the event lifetime.
- **Bound consumer responsibility.** Name affected consumers, side effects, idempotency, retry or terminal recovery, authorization, and the point where consumer failure no longer blocks the producer's business transition.
- **Prove transition-to-consumer behavior.** Exercise commit and publication crash windows, duplicate and reordered delivery, schema evolution, replay, consumer failure, and externally owned paths relevant to the task.

## Anti-Patterns

- Emit a generic entity-changed message with no precise fact, producer authority, subject identity, or compatibility meaning.
- Put a mutable domain object or broad sensitive snapshot in the payload because consumers might need it later.
- Assume broker order or acknowledgement proves business commit, unique effect, or consumer recovery.

## Stop Conditions

Escalate when fact meaning or producer authority is ambiguous, publication can diverge from committed state, or payload crosses privacy or tenant boundaries. Also escalate when consumer identity or ordering is unknown, schema history blocks replay, or consequential consumer effects lack recovery ownership.

## Output Contract

- domain-event decision with fact meaning, producer and commit boundary, subject and payload contract, identity and ordering, compatibility, consumer responsibilities, failure evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Commit, schema, ordering, replay, or payload mechanisms remain open | The signal is not a durable domain fact | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Event changes producer commits, consumers, retries, or sensitive payloads | No domain event contract or delivery behavior changes | analysis-agent, task-agent | checklist-result, residual-risk |
| [event evidence freshness](references/event-evidence-freshness.md) | evidence-pattern | Event approval depends on fresh topology, contracts, or replay results | No event-catalog or consumer claim is being accepted | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
