---
name: event-driven-architecture
description: "`analysis-agent`/`task-agent`: use when event flow, ordering, idempotency, replay, backpressure, or eventual consistency changes; skip when no event-driven decision is needed."
---

# event-driven-architecture

## Registry Trigger

**Use when**

- design asynchronous event flow ordering idempotency replay and eventual consistency

**Do not use when**

- no task-local event driven architecture decision is required

## Skill Role

Define event meaning, producers and consumers, publication boundaries, delivery and ordering semantics, replay, backpressure, schema evolution, and topology evidence. Exclude broker configuration and consumer migration.

## High-Value Rules

- **Define event meaning and authority.** Name the business fact or request, authoritative producer, subject identity, occurrence time, schema source, and distinction from internal commands or transport envelopes.
- **Map the current topology.** Trace producers, publication points, channels, filters, partitions, consumers, side effects, dead or delayed paths, and external ownership using fresh configuration and code evidence.
- **Coordinate state change and publication.** Select an owned consistency pattern from mapped crash, loss, and duplication windows.
- **Specify delivery, identity, and ordering together.** Define repeat identity, partition or subject ordering, concurrency, deduplication scope, late arrival, gaps, and behavior when global order is unavailable.
- **Bound replay and backpressure.** Describe retention source, schema and key history, replay authorization, pacing, aggregate retry, poison data, consumer lag, overload disposition, and protection of live traffic.
- **Design for mixed consumer versions.** Preserve unknown fields and values, compatibility, defaults, event meaning, deprecation, and rollback readability across deployed and replayed populations.
- **Prove terminal effects and recovery.** Exercise duplicates, loss windows, reordering, consumer crash, retry exhaustion, replay, and partial downstream effects, and record unverified topology or managed-service behavior.

## Anti-Patterns

- Publish a vague data-change notification with no authoritative meaning, owner, subject identity, or compatibility contract.
- Claim reliable delivery from broker acknowledgement while state-to-publication or consumer-effect crash windows remain open.
- Add retries or replay without aggregate load, idempotency, poison-data, live-traffic, and terminal-disposition ownership.

## Stop Conditions

Escalate when topology or ownership is unknown, loss or duplication can cause consequential effects, ordering assumptions exceed the partition contract, or replay can resurrect invalid or deleted state. Also escalate when schema history is missing or overload and terminal recovery lack accountable owners.

## Output Contract

- event architecture decision with event meaning, topology, consistency boundary, delivery identity and ordering, replay and backpressure, compatibility, failure evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Delivery, ordering, workflow, replay, or backpressure mechanisms compete | No event topology or consistency decision changes | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Architecture changes producers, consumers, DLQs, schemas, or irreversible effects | No asynchronous event flow is affected | analysis-agent, task-agent | checklist-result, residual-risk |
| [topology evidence freshness](references/topology-evidence-freshness.md) | evidence-pattern | Topology approval depends on fresh contracts, drills, or lag evidence | No producer-consumer completeness claim awaits approval | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
