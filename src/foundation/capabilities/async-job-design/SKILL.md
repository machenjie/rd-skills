---
name: async-job-design
description: "`task-agent`/`review-agent`: use when jobs, workers, queues, schedules, retries, cancellation, or status visibility need design; skip when no async-job decision is required."
---

# async-job-design

## Registry Trigger

**Use when**

- design background jobs queues schedules workers retries and status visibility

**Do not use when**

- no task-local async job design decision is required

## Skill Role

Define job identity, acceptance and commit boundaries, lifecycle, scheduling, concurrency, retry, cancellation, progress, overload, terminal recovery, and evidence. Exclude broker mechanics and event architecture.

## High-Value Rules

- **Define logical job identity and authority.** Bind task meaning to tenant or subject, inputs, version, initiator, deduplication scope, and which current source may create, cancel, retry, or inspect the work.
- **Coordinate acceptance with durable intent.** Map crashes before and after request response, job record, enqueue, business effect, progress update, and acknowledgement so accepted work cannot disappear silently or execute twice.
- **Model lifecycle and unknown outcomes.** Define queued, leased or running, blocked, cancelling, completed, failed, exhausted, and repair states only where semantics differ, including stale leases and lost worker responses.
- **Bound concurrency and scheduling.** Derive worker, tenant, key, dependency, priority, fairness, deadline, and overlap controls from current side effects, capacity, and ordering requirements.
- **Coordinate retry and cancellation with effects.** Distinguish transient, permanent, unknown, and partial outcomes; preserve idempotency, aggregate retry budget, cancellation races, cleanup, and late completion behavior.
- **Expose progress and terminal recovery.** Make status meaningful, monotonic where promised, attributable to current attempts, and connected to reconciliation, compensation, quarantine, manual repair, or accepted loss with an owner.
- **Prove crash and overload paths.** Exercise duplicate acceptance, worker death, timeout, cancellation, retry exhaustion, poison input, queue saturation, and recovery relevant to the changed job.

## Anti-Patterns

- Return acceptance before durable intent exists or infer completion from enqueue or worker acknowledgement alone.
- Retry non-idempotent partial work, or let cancellation imply an effect stopped when commit status remains unknown.
- Hide exhausted work in an unowned queue, generic failed state, or alert with no repair or disposition path.

## Stop Conditions

Escalate when job identity is ambiguous, acceptance can lose work, partial effects cannot reconcile, cancellation races are unsafe, or concurrency can violate invariants. Also escalate when overload is unbounded or terminal work lacks an accountable recovery owner.

## Output Contract

- async-job decision with identity and authority, durable acceptance, lifecycle, concurrency, retry and cancellation, progress, overload and terminal recovery, failure evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Durability, retry, acknowledgement, or recovery mechanisms remain undecided | Synchronous execution already satisfies accepted loss semantics | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Job design spans duplicates, leases, cancellation, replay, or deploy skew | A single bounded attempt has no durable side effects | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Job safety claims require fresh topology and failure-path results | No durability or replay claim needs closure evidence | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
