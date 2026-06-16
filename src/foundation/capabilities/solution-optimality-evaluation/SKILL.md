---
name: solution-optimality-evaluation
description: Requires every implementation decision to be explicitly challenged for justification, alternatives, and optimality across algorithm complexity, code architecture, ten performance dimensions (CPU, memory, network, disk, locks, TPS/QPS, parallelism, concurrency, latency, rendering), code quality, and system properties before the approach is locked.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "82"
changeforge_version: 0.1.0
---

# Mission

**Prevent premature lock-in on suboptimal design by requiring every significant implementation decision to pass a structured self-challenge before it is accepted.** This capability enforces three questions before any approach is finalized — *Why this way? Is this optimal? What is the better alternative?* — and then validates the answer across ten performance dimensions, four code-quality dimensions, and five system-property dimensions. It does not mandate a single "correct" answer; it mandates that the question is asked and that the chosen answer is justified with evidence, not assumed correct by default.

# When To Use

Use this capability when: a new algorithm, data structure, or processing strategy is being selected; a significant design decision affects performance, scalability, or maintainability; a builder or reviewer skill must assess the optimality of proposed or existing code; a performance-sensitive path (hot path, critical user flow, batch job, rendering path) is being designed or modified; code is being accepted that will be maintained by others for years; or a change creates resource consumption patterns whose magnitude is unknown or unverified.

# Do Not Use When

Do not use this capability for: trivial one-liner mechanical fixes with no design decision surface; pure cosmetic formatting or style changes; documentation edits; configuration values specified by an external requirement; or early throw-away prototypes explicitly scoped to prove feasibility only (must be re-evaluated before any prototype enters production code paths).

# Non-Negotiable Rules

- **The three-challenge rule**: Before locking any significant design decision, explicitly answer: (1) Why is this the right approach for this specific problem and context? (2) Is this the simplest design that satisfies all current requirements without speculation? (3) What is the strongest alternative, and why is it rejected with a specific, concrete reason? If none of these questions can be answered, the decision is not ready to implement.
- **Deletion/reuse challenge**: Before optimizing or expanding a solution, ask whether the correct answer is to delete code, reuse existing code, use a standard-library or native platform feature, shrink scope, or keep a local direct implementation. A more elaborate solution is not optimal when a simpler current option satisfies the same requirement and safety gates.
- **Measure before optimizing; never optimize by intuition alone**: A hypothesis that "this is slow" is the beginning of investigation, not the end. Profile first. The bottleneck revealed by measurement frequently differs from the initial hypothesis. Optimizing the wrong layer wastes time and introduces new defects.
- **Hot path analysis precedes optimization**: Identify whether the code being evaluated is on the critical path (called thousands of times per second) or the cold path (called once per day). Optimization effort must be proportional to frequency and production impact — premature optimization of cold paths reduces readability without meaningful benefit.
- **The deferred optimization trap is a production incident waiting to happen**: "We can optimize it later" is an escalation signal, not an acceptable resolution. If the current approach is known to be unacceptable at production scale, it must be fixed or the condition must be explicitly documented (the exact threshold at which it becomes unacceptable and who owns the remediation).
- **Worst-case and average-case are both required**: Stating that an algorithm is O(n log n) average-case is insufficient if the pathological input (sorted data, adversarial input, full cache miss, cold start) produces O(n²) or worse. Define the expected input distribution and the worst-case behavior explicitly.
- **All ten performance dimensions must be explicitly evaluated or declared N/A with a one-line rationale for every builder skill output**: Skipping a dimension is not an option. A dimension marked N/A without rationale is treated as skipped and the output is incomplete.
- **Cognitive complexity is a first-class engineering constraint**: Code that requires 30 minutes to understand on first read will be misread under incident pressure. If an implementation is clever, it must be justified against a simpler alternative. Cognitive complexity ≤ 15 per function is the professional standard (SonarSource definition); functions above 25 must be decomposed.
- **Reversibility must be stated explicitly**: Is this decision reversible without data migration, customer impact, or downtime? Irreversible decisions require explicit acknowledgment and a higher bar of justification evidence.

# Industry Benchmarks

- **Knuth, "The Art of Computer Programming"**: Algorithm analysis foundations — time complexity, space complexity, amortized analysis, average-case vs. worst-case. The full Knuth quote: "We should forget about small efficiencies, say about 97% of the time: premature optimization is the root of all evil. Yet we should not pass up our opportunities in that critical 3%." The 3% hot path must be optimized; the 97% cold path must be readable.
- **Brendan Gregg, "Systems Performance" (2nd ed., 2020)**: USE method (Utilization, Saturation, Errors) for every resource dimension; CPU flame graphs; off-CPU flame graphs (I/O wait, lock wait); bottleneck classification methodology.
- **Google SRE Book — Chapters 20–22**: Cascading failure prevention; distinguish load-induced vs. code-induced bottlenecks; identify resource constraints before tuning. Amdahl's Law applied to service-level parallelism.
- **DORA "Accelerate" (Forsgren et al.)**: Technical practices of elite teams: testability, deployability, loosely coupled architecture, trunk-based development. System properties of high-performing engineering organizations.
- **Martin Fowler, "Refactoring" (2nd ed.)**: Code smells and cognitive complexity. "Any fool can write code that a computer can understand. Good programmers write code that humans can understand."
- **C. A. R. Hoare, 1980 Turing Award Lecture**: "There are two ways of constructing a software design: one way is to make it so simple that there are obviously no deficiencies, and the other way is to make it so complicated that there are no obvious deficiencies." Simplicity is a correctness property.
- **Amdahl's Law**: Maximum speedup from parallelization = 1 / ((1 − p) + p/n), where p = parallel fraction, n = number of processors. If 20% of work is sequential, no amount of parallelization exceeds 5× speedup regardless of hardware.
- **Little's Law**: L = λW. Average concurrency (L) = arrival rate (λ) × average service time (W). Directly predicts required connection pool size, thread pool size, and queue depth from first principles.

### Self-Challenge Decision Framework

```
Step 1 — State the problem precisely (not the solution)
  Correct:  "We need to find all users inactive for 90 days from a 10M-row table."
  Incorrect: "We need to loop over all users and filter on last_login."

Step 2 — Generate at least 3 candidate approaches
  Candidate A: [approach] — O(?) time, O(?) space — key tradeoff: [...]
  Candidate B: [approach] — O(?) time, O(?) space — key tradeoff: [...]
  Candidate C: [approach] — O(?) time, O(?) space — key tradeoff: [...]

Step 3 — Eliminate with specific reasons (not "B is worse")
  A chosen because: [concrete evidence — benchmark, calculation, or structural argument]
  B rejected because: [specific cost — adds 40ms P99 latency, requires schema migration, etc.]
  C rejected because: [specific cost — O(n²) at production data volume, etc.]

Step 4 — Validate chosen approach against all 10 performance dimensions.

Step 5 — Check system properties (maintainability, extensibility, robustness, reversibility, testability).

Step 6 — Cognitive complexity check: can the next engineer understand this in < 10 minutes
          without reading the commit history?
```

### Ten Performance Dimensions — Evaluation Checklist

Every builder skill output must evaluate each dimension or explicitly declare it N/A with a one-line rationale:

| # | Dimension | Key Questions | Common Failure Mode |
|---|---|---|---|
| 1 | **CPU** | What is the algorithmic time complexity (O notation)? Are there hot loops with unnecessary work? Is serialization/deserialization on the critical path? Are regexes precompiled? Is reflection or dynamic dispatch used in a hot path? | O(n²) algorithm on a user-supplied list; uncompiled regex evaluated per request; JSON re-serialized inside a tight loop |
| 2 | **Memory** | What is the space complexity? Are large objects allocated per-request when they could be pooled? Is GC pressure acceptable (allocation rate per RPS in garbage-collected runtimes)? Are there potential memory leaks — event listeners not removed, timers not cleared, growing caches without eviction bounds? | Unbounded in-memory accumulation; per-request large allocation at 5k RPS triggers GC pause spikes; global cache grows without TTL or max-size |
| 3 | **Network** | How many network round trips does this trigger per user action? Is the payload size bounded? Are connections reused (keep-alive, connection pooling)? Is there an N+1 HTTP fan-out or N+1 database query pattern? | N+1 HTTP calls in a loop; large unbounded response payload; synchronous external call on hot path with no timeout |
| 4 | **Disk** | What is the read/write pattern (sequential vs. random)? Is fsync necessary on every write or can it be batched? Is write amplification acceptable for the storage engine (LSM tree WAL, PostgreSQL WAL, log flush)? Are log volumes bounded? | Synchronous fsync per record write; unbounded log verbosity; random I/O on large index without SSD |
| 5 | **Locks / Contention** | What shared mutable state is accessed? Is lock scope minimized (lock held only while accessing shared state, not across I/O)? Is optimistic locking preferred over pessimistic for low-conflict cases? Is lock ordering consistent across code paths (deadlock prevention)? Is false sharing possible (two fields on the same CPU cache line accessed by different threads)? | Pessimistic lock held across a remote API call; inconsistent lock acquisition order in two code paths causes deadlock at high concurrency; false sharing in a concurrent counter struct |
| 6 | **TPS / QPS** | What is the throughput ceiling of this design? Is it calculated (Little's Law: required pool ≥ target RPS × avg service time)? Does the design scale linearly with traffic? Where is the first bottleneck resource? | Connection pool sized at default (10) while target RPS requires 50; no throughput ceiling defined; sequential bottleneck in an otherwise parallel processing pipeline |
| 7 | **Parallelism** | Can work be safely partitioned and executed in parallel? What is the maximum achievable speedup (Amdahl's Law: 1/(1−p))? Is the sequential fraction quantified? Is the parallel coordination overhead justified for the expected input sizes? | Parallelizing a job where 70% of work is sequential — maximum speedup is 3.3× regardless of thread count; parallel overhead exceeds benefit for small batches |
| 8 | **Concurrency** | Are all shared state accesses thread-safe? Is a time-of-check-to-time-of-use (TOCTOU) race possible? Is a thundering herd or cache stampede risk addressed for cache-backed or connection-backed paths? Is there a goroutine / thread / coroutine leak? | Race condition on shared counter; thundering herd when cache item expires simultaneously for 500 concurrent users; connection leak when error path skips pool.release() |
| 9 | **Response Latency** | Are P50/P95/P99 targets defined and validated at expected concurrency? Is tail latency amplification considered for fan-out (P99_aggregate worsens as N parallel calls increase)? Does the chosen approach meet the SLO under load, not just in development? | P99 target undefined; fan-out to 8 downstream services at P99=50ms each raises aggregate latency significantly; SLO only validated at P50 or on a single-threaded local test |
| 10 | **Rendering Speed** | (Frontend only) Is main thread work bounded to < 50ms per task (Long Tasks API)? Are INP/LCP/CLS within Core Web Vitals budget? Are expensive re-renders memoized? Is layout thrashing (read-style then write-style in a loop) prevented? | Synchronous heavy computation on main thread during user interaction; unnecessary full subtree re-render cascade; forced synchronous layout from mixing DOM reads and writes |

### Additional Professional-Level Engineering Considerations

These considerations are frequently missed but regularly cause production incidents in mature systems:

**Data Locality and CPU Cache Efficiency**
- L1 cache hit latency ≈ 4 cycles; L2 ≈ 12 cycles; L3 ≈ 40 cycles; main memory ≈ 200 cycles. A cache-unfriendly access pattern (random pointer chasing through linked structures) can be 50× slower than a cache-friendly sequential scan even with the same asymptotic complexity.
- Array-of-Structs (AoS) vs. Struct-of-Arrays (SoA): for code that iterates over all objects processing one field, SoA packs that field contiguously in memory (cache-friendly); AoS interleaves all fields (cache-unfriendly for single-field scans).
- Hot data and cold data should be separated so the working set fits in L3 cache.

**Back-Pressure and Graceful Degradation**
- When upstream producers generate load faster than downstream consumers can process, three outcomes are possible: (a) unbounded queue → OOM; (b) no queue → immediate rejection; (c) bounded queue with back-pressure → graceful degradation (preferred). Design for (c) explicitly.
- Return `503 Service Unavailable` with `Retry-After` rather than allowing the system to degrade silently into timeout storms.
- Identify the concurrency level at which the system transitions from "slow but functional" to "non-functional." This threshold must be above expected peak load or load-shedding must activate before it.

**Tail Latency Amplification in Fan-Out**
- When a request fans out to N parallel dependencies, the probability of the aggregate response exceeding P99_single is approximately 1 − (1 − 0.01)^N. At N=10, ~10% of aggregate requests experience at least one tail dependency. At N=69, the median (P50) aggregate latency equals P99_single.
- Mitigation: hedged requests (send a second request to a replica if the first is slow), reduced fan-out via caching or aggregation, or explicit tail latency SLO that accounts for the fan-out factor.

**Thundering Herd and Cache Stampede**
- When a popular cached item expires and hundreds of concurrent requests simultaneously miss the cache, all requests hit the backing store at once. Mitigations: probabilistic early expiration (XFetch / PER algorithm), mutex-on-refill (only one request rebuilds the cache; others wait), or background async refresh before expiry.
- Service restart thundering herd: when a service restarts after a cold start, all cache misses arrive at the backing store simultaneously. Mitigation: staggered warm-up, request coalescing, read-through with single-flight pattern.

**Hot Key / Hot Partition Problem**
- In sharded or partitioned systems (consistent hash ring, Kafka partitions, Redis Cluster, DynamoDB), a key that receives disproportionate traffic becomes a hot spot that limits overall system throughput to the throughput of that single partition.
- Detection: per-partition traffic metrics, p99 latency divergence across partitions.
- Mitigation: key salting (append random suffix, fan-out reads), local replica caching, explicit hot-key detection and routing.

**Connection Pool Sizing — Little's Law**
- Required pool size ≥ (target RPS) × (average service time in seconds). Example: a database with 20ms average query time serving 500 RPS requires ≥ 500 × 0.02 = 10 connections at steady state. Add headroom for burst: multiply by 1.5–2×. Under-sized pools cause request queue buildup; over-sized pools exhaust the server's connection limit.
- Validate pool size against production workload, not local test assumptions.

**GC Pressure and Allocation Rate**
- In garbage-collected runtimes (JVM, Go, Node.js, .NET), high per-request object allocation causes GC pause spikes that directly translate to P99 latency spikes visible only under load — invisible in developer testing.
- Profile allocation rate per endpoint using JVM Flight Recorder, Go pprof heap, or Node.js `--heap-prof`. Reduce per-request allocation in hot paths: use object pooling, pre-allocated buffers, avoid string concatenation in loops (use builders / StringBuilder / bytes.Buffer).
- Long-lived objects promoted to old generation (JVM tenured / Go non-escapable heap) increase full-GC frequency. The allocation site that fills the old gen is often surprising — measure it.

**False Sharing in Concurrent Code**
- Two fields accessed by different CPU cores but residing on the same 64-byte CPU cache line cause cache invalidation on every write to either field, effectively serializing access. Symptom: unexpectedly high contention on variables that are independently updated.
- Mitigation: cache-line padding, separating hot per-thread state into distinct cache-line-aligned structures, or use of lock-free primitives that avoid the shared line.

**Cognitive Complexity (Beyond Cyclomatic Complexity)**
- Cyclomatic complexity counts decision branches. Cognitive complexity (SonarSource metric) adds a penalty for nesting depth, non-linear flow breaks (`break`, `continue`, `goto`, early return from deep nesting), and recursive calls. A function with cyclomatic complexity 10 in a flat structure is far easier to maintain than one with cyclomatic complexity 5 but triple-nested conditionals.
- Professional standard: cognitive complexity ≤ 15 per function. Functions > 25 must be decomposed before handoff. Functions > 40 are an on-call incident risk, not a code review note.

**Reversibility Classification**
- **Reversible**: configuration changes, feature flags, additive schema changes — can be undone with a deploy or toggle within minutes.
- **Conditionally reversible**: database migrations with backward-compatible changes — can be rolled back within the migration window before the old code is retired.
- **Irreversible**: destructive schema changes (`DROP COLUMN`), cryptographic key rotation without old-key retention, event stream schema changes without upcasters, data deletion, published breaking API changes — require explicit sign-off, rollback simulation, and sunset planning.

**Testability as a Design Property**
- Code that requires global state, singletons, or hardcoded external dependencies cannot be unit-tested in isolation. If a function cannot be tested without a running database, message queue, or external HTTP service, the design has testability debt that accumulates interest with every copy-paste of the pattern.
- Observable design: every significant decision should produce a measurable side effect (metric emitted, structured log written, state transitioned) that can be asserted in tests and diagnosed in production.

**Security Surface Expansion**
- Every new endpoint, parameter, file path, command argument, or code branch is a potential attack vector. Does the new code increase the set of inputs an attacker can influence? Are all new inputs validated at trust boundaries? Does the new code path require new authorization checks that the existing path does not have?
- Every dependency added expands the supply chain attack surface. Evaluate transitive dependency depth and recent CVE history before accepting a new dependency, regardless of how small the dependency appears.

**Operational Cost Awareness**
- In cloud-hosted systems, algorithm choices and data access patterns have direct cost implications: N+1 queries translate to N× database read units (DynamoDB RCUs, Aurora ACUs, BigQuery bytes scanned); large object scans translate to GB transferred and billed; unnecessary recomputation translates to CPU billing per millisecond.
- Cost-per-request and latency-per-request are both engineering constraints in production. Algorithms that are fast but wasteful are not free.

# Selection Rules

Apply this capability when an implementation choice is non-trivial (more than one reasonable approach exists) and the stakes are non-trivial (production traffic, data integrity, security, or multi-year maintainability). The three-challenge rule applies to all builder skill outputs. The ten-dimension checklist applies to every change that touches a performance-sensitive path, resource allocation, or concurrency model. It is not optional.

# Risk Escalation Rules

- Escalate to `profiling` when a performance dimension evaluation identifies an unknown bottleneck that cannot be assessed without measurement data from representative load.
- Escalate to `performance-budgeting` when no latency, throughput, or resource budget exists for the component being designed, and one must be established before the evaluation can be completed.
- Escalate to `architecture-impact-reviewer` when the optimality evaluation reveals that the best approach requires a structural change to the system architecture (new boundary, new service, dependency direction change).
- Escalate to `data-middleware-change-builder` when database query patterns, indexing strategies, lock contention, or storage engine behavior require expert evaluation.
- Escalate to `reliability-observability-gate` when the evaluated change affects SLI/SLO-bound production paths.
- Escalate when cognitive complexity analysis reveals code that cannot be safely maintained — refactoring is required before handoff.

# Critical Details

- The most common optimality failure is not choosing a bad algorithm — it is failing to ask the question at all. The default is to accept the first working approach. This capability makes "first working" an insufficient standard.
- O(n²) algorithms in production code are not theoretical concerns: 10,000 items → 100M operations; 100,000 items → 10B operations. Always identify the production-scale input size before accepting an algorithm.
- The ten performance dimensions are not independent. Optimizing for CPU may increase memory (memoization trades memory for CPU cycles). Optimizing for throughput may increase latency variance (batching reduces per-unit CPU at the cost of higher average latency). Explicitly document the tradeoff accepted.
- Fan-out tail latency is the most consistently underestimated production problem. Engineers test a single downstream call, measure P99=50ms, and declare performance acceptable — without modeling that 10 parallel calls at P99=50ms each creates an aggregate tail latency problem affecting a significant percentage of all requests.
- Deferred optimizations accumulate interest. Each "we'll fix it later" increases the cost of the fix as surrounding code grows, tests multiply, and the pattern is copied. Professional discipline: fix it now or document the threshold at which it must be fixed with a named owner.

# Failure Modes

- **Algorithm accepted on first-pass plausibility**: A correct O(n²) sort accepted because it "works in tests" — tests use 10 records; production has 10 million.
- **Performance dimensions skipped**: Latency and throughput were checked; memory was not — the new batch job causes OOM in its first production run.
- **Deferred optimization never revisited**: "We'll optimize when it becomes a problem" — the problem arrives at 2 AM during peak traffic, not during a planned engineering sprint.
- **Fan-out tail latency not modeled**: A feature calls 12 downstream services; P99 was measured per-service but not for the aggregate response.
- **Thundering herd on cache invalidation**: Cache was cleared on deploy; all 800 concurrent users hit the database simultaneously; the database ran out of connections.
- **Cognitive complexity exceeded**: A "clever" bitwise-and-ternary implementation reduced CPU by 3% but required a 45-minute onboarding session — maintainers copied it incorrectly in the next sprint.
- **GC pressure invisible in development**: Per-request object allocation looked fine locally; at 2,000 RPS, GC pause spikes appeared as 200ms P99 spikes visible only in production load testing.
- **Irreversible decision without acknowledgment**: A destructive schema migration was applied; a rollback was triggered for an unrelated reason; the dropped column data was permanently lost.
- **Hot key undetected**: A new feature hashed all new users to the same Kafka partition; one partition's consumer was the bottleneck for the entire pipeline.
- **False sharing in concurrent counter**: Two independent counters placed adjacently in a struct caused cache-line thrashing at 200 concurrent threads — performance degraded worse than a single-threaded baseline.

# Output Contract

Return an optimality evaluation that includes:
- **Three-challenge answers**: (1) Why this approach — specific evidence. (2) Is it the simplest sufficient design — yes/no with rationale. (3) Strongest alternative rejected — name it, state the specific cost.
- **Deletion/reuse answer**: delete, reuse, stdlib/native, existing dependency, local direct code, or new implementation decision, with the specific reason the simpler option is accepted or rejected.
- **Ten-dimension assessment**: For each dimension: rating (✓ Satisfactory / ⚠ Risk / ✗ Unacceptable / N/A with one-line rationale), key evidence, and any required action.
- **Additional considerations applied**: Which (if any) of the additional professional considerations apply and the finding.
- **Cognitive complexity assessment**: ≤ 15 per function (pass) / > 15 and ≤ 25 (note decomposition opportunity) / > 25 (decomposition required before handoff).
- **Reversibility classification**: Reversible / Conditionally reversible / Irreversible — with one-line rationale.
- **Optimization deferral log**: If any dimension is accepted as "not optimal but currently acceptable," document the threshold condition and named owner for revisit.

# Quality Gate

1. All three challenge questions are answered with specific evidence, not assertions.
2. All ten performance dimensions are evaluated or declared N/A with a one-line rationale.
3. At least one alternative approach is explicitly named and rejected with a specific cost reason.
4. Cognitive complexity of the chosen implementation is ≤ 15 per function, or a decomposition plan is specified for functions exceeding 25.
5. Reversibility classification is stated.
6. Any accepted "deferred optimization" has a documented threshold condition and a named owner for revisit.

# Used By

backend-change-builder, frontend-change-builder, data-api-contract-changer, data-middleware-change-builder, integration-change-builder, ai-code-review-refactor, architecture-impact-reviewer, reliability-observability-gate, change-impact-analyzer

# Handoff

- **profiling** — when measurement under representative load is needed to answer performance dimension questions.
- **performance-budgeting** — when budgets are undefined and must be established before evaluation proceeds.
- **architecture-impact-reviewer** — when the evaluation reveals a required structural change.
- **data-middleware-change-builder** — when database-layer performance analysis (query plans, index design, lock contention) requires depth beyond this capability's scope.

# Completion Criteria

The evaluation is complete when: all three challenge questions have justified answers with specific evidence; all ten performance dimensions have been assessed with evidence or declared N/A with rationale; the cognitive complexity is within bounds or a decomposition is proposed for out-of-bounds functions; the reversibility classification is stated; and any accepted deferred optimizations have a documented threshold condition.
