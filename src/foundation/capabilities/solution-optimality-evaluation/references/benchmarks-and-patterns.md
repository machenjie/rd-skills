# Solution Optimality Benchmarks And Patterns

Use this reference when `solution-optimality-evaluation` needs more depth than the main `SKILL.md` can carry efficiently. Keep the skill body focused on routing, decision rules, output, and gates; use this file for benchmark anchors, the self-challenge workflow, performance-dimension details, and advanced failure patterns.

## Table Of Contents

- Benchmark anchors
- Self-challenge decision framework
- Ten performance dimensions
- Professional engineering considerations
- Evidence patterns
- Anti-patterns to reject
- Handoff boundaries

## Benchmark Anchors

- **Algorithm analysis practice:** time complexity, space complexity, amortized analysis, average-case and worst-case behavior, and input-distribution assumptions.
- **Systems performance practice:** USE method for resource utilization, saturation, and errors; CPU and off-CPU profiling; bottleneck classification before tuning.
- **SRE practice:** cascading failure prevention, load-induced vs. code-induced bottlenecks, resource constraints, capacity planning, and Amdahl's Law for service-level parallelism.
- **DORA / Accelerate:** testability, deployability, loosely coupled architecture, and fast recovery as system properties affected by design choices.
- **Refactoring and cognitive complexity:** readability, code smells, decomposition, and the maintainability cost of clever implementations.
- **Simplicity as correctness:** designs should be simple enough to inspect; complexity needs concrete current requirements, not speculative future fit.
- **Amdahl's Law:** parallel speedup is capped by the sequential fraction; if 20% of work is sequential, speedup cannot exceed 5x regardless of hardware.
- **Little's Law:** average concurrency equals arrival rate multiplied by service time; use it to size pools, workers, queues, and in-flight work.

## Self-Challenge Decision Framework

```
Step 1 - State the problem precisely, not the solution.
  Correct:  "Find users inactive for 90 days from a 10M-row table."
  Incorrect: "Loop over all users and filter on last_login."

Step 2 - Generate at least 2 candidate approaches, ideally 3 for material decisions.
  Candidate A: [approach] - O(?) time, O(?) space - key tradeoff: [...]
  Candidate B: [approach] - O(?) time, O(?) space - key tradeoff: [...]
  Candidate C: [approach] - O(?) time, O(?) space - key tradeoff: [...]

Step 3 - Eliminate with specific reasons.
  A chosen because: [benchmark, calculation, structural evidence, or constraint]
  B rejected because: [specific cost: P99 latency, migration, O(n^2), owner burden]
  C rejected because: [specific cost or constraint]

Step 4 - Validate the chosen approach against all relevant performance dimensions.

Step 5 - Check system properties: maintainability, extensibility, robustness,
          reversibility, testability, security surface, and operational cost.

Step 6 - Check graph, memory, and execution freshness.
  Source and registry current? Memory accepted/rejected? Validation after final edit?
```

## Ten Performance Dimensions

Every builder or reviewer output must evaluate each applicable dimension or declare it N/A with a one-line rationale.

| # | Dimension | Key questions | Common failure mode |
| --- | --- | --- | --- |
| 1 | CPU | What is the algorithmic complexity? Are hot loops doing unnecessary work? Is serialization, regex, reflection, or dynamic dispatch on the critical path? | O(n squared) work on user-supplied collections; per-request JSON reserialization inside a loop. |
| 2 | Memory | What is the space complexity? Are allocations bounded? Is cache size/TTL defined? Is object retention or listener/timer cleanup safe? | Unbounded accumulation; per-request large allocation creates GC pause spikes; cache without eviction. |
| 3 | Network | How many network round trips occur per user action? Are payloads bounded? Is fan-out or N+1 I/O introduced? | Batched call replaced with per-item calls; synchronous external call on a hot path with no timeout. |
| 4 | Disk | Are reads/writes sequential or random? Is fsync required per write? Is log volume bounded? Is scan size controlled? | Synchronous fsync per record, unbounded logs, or random I/O over a large index. |
| 5 | Locks / contention | What shared state exists? Is lock scope minimal? Is lock ordering consistent? Is false sharing possible? | Lock held across remote I/O; deadlock under high concurrency; cache-line contention on counters. |
| 6 | TPS / QPS | What is the throughput ceiling? Is pool/worker size derived from Little's Law? Where is the first bottleneck? | Default pool size is too small for target RPS; no saturation point defined. |
| 7 | Parallelism | Can work be partitioned safely? What is the sequential fraction? Does coordination cost exceed benefit for expected sizes? | Parallel job where most work is sequential; worker overhead exceeds benefit for small batches. |
| 8 | Concurrency | Are shared accesses safe? Can TOCTOU, thundering herd, duplicate work, or leak occur? | Race condition, cache stampede, unbounded worker spawn, or error path skips release/cleanup. |
| 9 | Response latency | Are P50/P95/P99 targets defined at expected concurrency? Is fan-out tail latency modeled? | Per-service P99 accepted without aggregate fan-out modeling. |
| 10 | Rendering speed | For frontend paths, is main-thread work bounded, layout thrash avoided, and Core Web Vitals budgeted? | Heavy sync work during input, full subtree re-render cascade, or forced layout loops. |

## Professional Engineering Considerations

### Data Locality And CPU Cache Efficiency

- L1, L2, L3, and main-memory latency differ enough that cache-unfriendly pointer chasing can lose to a contiguous scan with the same asymptotic complexity.
- Array-of-Structs vs. Struct-of-Arrays matters when hot loops touch one field across many records.
- Separate hot and cold data so the working set fits in cache when the path is truly performance-sensitive.

### Back-Pressure And Graceful Degradation

- Unbounded queues become memory incidents; no queue becomes immediate rejection; bounded queues with back-pressure give controlled degradation.
- Prefer explicit `503` plus `Retry-After`, admission control, or load shedding over silent timeout storms.
- Name the concurrency level where the system shifts from slow-but-functional to non-functional.

### Tail Latency Amplification In Fan-Out

- A request that fans out to many dependencies has a much worse aggregate tail than one dependency's P99 suggests.
- Mitigate with reduced fan-out, caching, aggregation, hedged requests, or a tail-latency SLO that accounts for fan-out count.

### Thundering Herd And Cache Stampede

- Popular cache expiry, deploy-time cache clearing, and service restarts can send all traffic to the backing store at once.
- Use request coalescing, mutex-on-refill, probabilistic early expiration, staggered warm-up, or background refresh.

### Hot Key / Hot Partition

- One high-traffic key can limit a sharded system to one partition's capacity.
- Detect with per-partition metrics and p99 divergence; mitigate with salting, replica caching, or explicit hot-key routing.

### Connection Pool Sizing

Use Little's Law:

```
required_pool_size >= target_rps * average_service_time_seconds * safety_factor
```

Validate with pool wait time, saturation, queue depth, and tail latency. Defaults are not evidence.

### GC Pressure And Allocation Rate

- High allocation per request creates latency spikes only visible under load in garbage-collected runtimes.
- Profile allocation rate and heap growth; reduce hot-path allocation with reuse, streaming, preallocation, or simpler data shapes.
- Long-lived retained objects can promote into older generations and increase full-GC frequency.

### Cognitive Complexity

- Cyclomatic complexity counts branches; cognitive complexity penalizes nesting and non-linear flow.
- Professional standard: cognitive complexity <= 15 per function. Values above 25 require decomposition or explicit exception; values above 40 are operational risk.

### Reversibility Classification

- **Reversible:** configuration changes, feature flags, additive schema changes, or localized implementation swaps.
- **Conditionally reversible:** backward-compatible migrations, dual-write/dual-read windows, or phased dependency replacement.
- **Irreversible:** destructive data changes, breaking public contracts, one-way key rotation, event-stream changes without upcasters, or customer-visible migrations without rollback.

### Testability, Security Surface, And Cost

- A design that cannot be tested without global state or hardcoded external systems carries structural testability debt.
- New endpoints, parameters, dependencies, file paths, commands, and prompt/tool branches expand security surface.
- N+1 I/O, query scans, fan-out, egress, retry storms, and recomputation are cost decisions as well as performance decisions.

## Evidence Patterns

- Algorithm path: candidate list, input distribution, O-time/space, selected data structure, benchmark/profile need, rejected simpler option.
- API or service flow: latency/throughput budget, dependency fan-out, retry budget, SLO impact, validation after final edit.
- Database path: current SQL/ORM source, representative plan, rows examined/returned, index/lock decision, handoff to query optimization when needed.
- Batch or worker path: input volume, checkpoint/retry behavior, CPU/RSS ceiling, queue depth, wall-clock window, restart behavior.
- AI refactor: before/after complexity, hidden I/O scan, allocation/concurrency review, hallucinated API check, tests tied to changed paths.
- Skill or routing change: baseline score/audit, treatment diff, reference loading budget, structural-vs-empirical caveat, full validation.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| "Works in tests" as optimality proof. | Fixtures often hide production-scale input, contention, and resource cost. |
| Strongest alternative omitted. | No reviewer can verify the tradeoff when the rejected choice is unnamed. |
| "Fast enough" with no budget. | Untestable and easy to regress. |
| Mean latency only. | Hides tail latency and fan-out amplification. |
| Unbounded memoization/cache. | Converts CPU improvement into memory leak. |
| Generic abstraction for one use case. | Adds permanent maintenance cost for speculative future flexibility. |
| Old memory or report as proof. | Selector evidence can go stale after source, traffic, schema, or validation changes. |
| Validation before final edit. | The evidence covers a different artifact than the handoff describes. |
| Optimization deferral without owner and threshold. | Becomes an incident-driven rewrite rather than planned work. |

## Handoff Boundaries

- Use `algorithm-data-structure-selection` when the selected structure, traversal, streaming/chunking, cache, or index choice needs deeper analysis.
- Use `performance-budgeting` when the budget itself is missing.
- Use `profiling` when the bottleneck is unknown or disputed.
- Use `language-performance-safety` when runtime allocation, GC, event loop, pool, lock, native, or unsafe boundary risk dominates.
- Use `reliability-observability-gate` when SLO, alerting, capacity, fallback, or production reliability semantics are affected.
- Use `architecture-impact-reviewer` when the chosen approach changes ownership, service boundaries, dependency direction, or long-term topology.
- Use `security-privacy-gate` when the optimal choice expands trust, input, dependency, file, command, prompt, data, or authorization surface.
- Use `quality-test-gate` and `validation-broker` when changed paths need mapped tests, benchmarks, builds, or stale-validation repair.
