---
name: message-queue-design
description: "`task-agent`/`review-agent`: use when broker delivery, ordering, acknowledgement, DLQ, backpressure, or replay changes; skip synchronous retry without message semantics."
---

# message-queue-design

## Registry Trigger

**Use when**

- design queues topics consumers ordering retries dead letters and backpressure
- Kafka topic partition consumer group offset commit schema registry retention compaction DLQ consumer lag replay transactional outbox Kafka Connect

**Do not use when**

- no task-local message queue design decision is required
- synchronous request retry without broker or message-delivery semantics

## Skill Role

Protect broker delivery, acknowledgement, ordering, retry, terminal disposition, replay, and backpressure semantics.

## High-Value Rules

- Verify actual delivery, acknowledgement or visibility, ordering, retention, redelivery, and replay semantics.
- Do not treat synchronous request retry alone as a queue-contract trigger.
- Place acknowledgement after the durable boundary required by the business effect, and select manual commit, transactional consumption, idempotency, dedupe, or reconciliation only when crash/redelivery semantics and irreversible effects justify them.
- Classify transient, permanent, malformed, and poison failures by retry eligibility and terminal disposition.
- Derive retry eligibility, attempts, and delay from current broker and workload evidence.
- Select an owned terminal disposition for every class. Treat DLQ as one candidate beside quarantine, pause, policy-permitted rejection, compensation, or manual repair.

## Anti-Patterns

- Broker deduplication windows and exactly-once labels rarely cover downstream side effects, late replay, disaster recovery, or a consumer crash between effect and acknowledgement.
- Treat a DLQ as hidden failed work unless it has an owner, alert condition, safe inspection, retention, and a replay or repair procedure.
- Limit broker redelivery attempts because retries can amplify outages and block ordered partitions.

## Execution Checklist

1. Map producer, consumer, delivery guarantee, acknowledgement/visibility point, ordering key, schema/version, duplicate window, replay sources, and irreversible effects.
2. Classify failure and poison behavior, then select only triggered, broker-supported acknowledgement, retry or no-retry, terminal disposition, backpressure, idempotency, ordering, and recovery controls.
3. Validate every remaining triggered broker risk.
4. Record unavailable checks and their proof limits.

## Stop Conditions

- Escalate financial/regulated/security events, irreversible non-idempotent effects, unclear ordering, unsafe replay, unowned terminal disposition, or expected lag beyond the owned objective when broker evidence or recovery ownership is missing.

## Output Contract

- message queue plan with topology, ordering, and acknowledgement; selected retry or no-retry policy; terminal disposition and owner; replay and triggered-metrics evidence with proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [broker benchmarks](references/broker-benchmarks.md) | benchmark-pattern | delivery ordering rebalance visibility replay or backpressure semantics need a broker mechanism choice | the task is synchronous and has no broker delivery semantics | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A queue-topology, producer, or consumer change affects acknowledgement or visibility, concurrent duplicates, ordering or partition skew, schema evolution, replay, retries, or terminal disposition | broker semantics and handler behavior remain unchanged and proven | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | delivery idempotency lag or replay claims need current artifacts | fresh broker config and crash-path tests prove each claim | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
