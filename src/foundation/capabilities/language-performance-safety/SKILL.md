---
name: language-performance-safety
description: "`analysis-agent`/`task-agent`/`review-agent`: use when allocation, GC, concurrency, async/blocking, FFI, or unsafe/native behavior changes; skip when runtime safety is unaffected."
---

# language-performance-safety

## Registry Trigger

**Use when**

- language performance safety allocation GC async blocking FFI unsafe native hot path memory concurrency event loop runtime constraints
- CPU-bound, storage IO, network IO, file IO, blocking IO, non-blocking IO, coroutine, goroutine, thread pool, worker pool, lock held across IO, event-loop blocking, unbounded fan-out, pool sizing, per-operation client construction, response body leak, object allocation regression, design pattern performance risk

**Do not use when**

- no task-local language performance safety decision is required

## Skill Role

Define measured runtime cost, allocation and retention shape, scheduler interaction, blocking, cancellation, backpressure, resource lifecycle, concurrency evidence, and foreign-interface safety. Exclude architecture and production reliability claims.

## High-Value Rules

- **Measure the risk-carrying workload before optimizing.** Bind each claim to the current workload, metric, profile or trace, environment, versions, and before/after comparison; label unmeasured expectations as hypotheses.
- **Trace allocation through retention and collection.** Distinguish allocation rate, retained memory, copying, fragmentation, and collection effects, then compare them with task-specific latency and capacity objectives.
- **Protect scheduler and blocking boundaries.** Move blocking or CPU-heavy work away from latency-sensitive executors where current runtime semantics require it, and define bounded admission, cancellation, and overload behavior.
- **Bound growth and fan-out.** Derive limits for buffers, batches, queues, caches, retries, tasks, and per-request work from trusted inputs, observed distribution, capacity evidence, and failure consequence.
- **Own reusable resource lifecycle.** Define client, pool, stream, cursor, subscription, timer, file, and lock ownership across success, error, timeout, cancellation, and shutdown, including refresh and cleanup behavior.
- **Prove concurrency outcomes.** Exercise races, contention, cancellation, queue saturation, and allowed terminal states with current stress or fault evidence; reasoning alone does not establish scheduler behavior.
- **Treat unsafe and foreign boundaries as explicit contracts.** Record ownership, lifetime, alignment, thread rules, error and unwind behavior, validation, and the specialist evidence needed for the changed boundary.

## Anti-Patterns

- Tune from runtime reputation, microbenchmark folklore, or a local average that omits tail, saturation, retention, and production workload differences.
- Replace an unbounded queue with a bounded one without defining reject, wait, shed, or recovery semantics.
- Improve apparent speed by leaking resources, weakening cancellation, widening unsafe scope, or hiding overload.

## Stop Conditions

Escalate when the workload or objective is unknown, profiling cannot distinguish the bottleneck, overload could lose or duplicate consequential work, or unsafe ownership is ambiguous. Also escalate when concurrency evidence is unavailable, cleanup is unbounded, or the change can materially alter latency, capacity, availability, or native safety.

## Output Contract

- runtime performance and safety decision with workload evidence, allocation and scheduler boundaries, growth limits, lifecycle ownership, concurrency proof, unsafe contract, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | profiling exposes competing allocation concurrency pooling or cleanup remedies | measurement and runtime constraints select one safe remedy | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | hot paths alter allocation bounds async blocking cleanup or unsafe code | change touches no measured performance or runtime-safety boundary | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | performance race cleanup or FFI claims need fresh runtime proof | current profiles stress checks and source evidence prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
