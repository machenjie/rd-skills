# Solution Optimality Self-Check — Backend Change Builder

Compiled from foundation capability `solution-optimality-evaluation`. Apply to every
backend change that touches a performance-sensitive path, resource allocation model, or
concurrency pattern. Loaded on demand per the skill's Reference Loading Policy.

**Three-Challenge Rule** — answer all three before finalizing any backend design:
1. **Why this approach?** State the concrete reason it satisfies the requirement better than the alternatives (not "it seemed natural").
2. **Is this the simplest sufficient design?** If a direct DB query replaces a cache + background job, use the simpler approach until profiling proves otherwise.
3. **What is the strongest alternative, and why is it rejected?** Name it. Reject it with a specific cost ("adds 40ms P99", "requires schema migration", "O(n²) at 500k records").

**Performance Dimension Checklist** — evaluate each or declare N/A with a one-line rationale:

| Dimension | Required Question | Backend-Specific Failure Mode |
|---|---|---|
| **CPU** | What is the time complexity (O notation)? Are there hot loops, precompile-required regexes, or unnecessary serialization per request? | O(n²) on a user-supplied list; regex evaluated per request without compilation; JSON re-serialized inside a loop |
| **Memory** | Are batch sizes bounded to prevent OOM? Is per-request heap allocation measured in GC-managed runtimes at target RPS? Does any global or long-lived structure lack eviction bounds? | Unbounded batch causing heap exhaustion; per-request allocation rate triggers GC pause spikes under load; in-memory map grows indefinitely |
| **Network** | Are N+1 database queries and N+1 HTTP fan-out patterns eliminated? Are bulk/batch calls used instead of per-item calls? | N+1 queries fetching related records in a loop; per-item HTTP POST instead of batch endpoint |
| **Disk** | Does the write pattern align with the storage engine's I/O model? Is WAL amplification acceptable? Are log volumes bounded? | Synchronous fsync per record; unbounded log verbosity at DEBUG level left in production |
| **Locks / Contention** | Is lock scope minimized (not held across I/O)? Is optimistic locking preferred for low-conflict cases? Is lock ordering consistent across all code paths (deadlock prevention)? | Pessimistic lock held across a remote API call; two code paths acquire locks in opposite order causing deadlock under concurrency |
| **TPS / QPS** | What is the throughput ceiling? Is pool size calculated via Little's Law (pool ≥ target RPS × avg service time in seconds)? Where does the first resource saturate? | Connection pool left at framework default (10) while target RPS requires 30+; no throughput ceiling defined for a new async job |
| **Parallelism** | Can background job work be safely partitioned? What is Amdahl's ceiling (1/(1−p)) given the sequential fraction? Is parallel coordination overhead justified at the expected batch size? | Parallelizing a job that is 70% sequential — maximum speedup is 3.3× regardless of thread count |
| **Concurrency** | Are all shared state accesses thread-safe? Is a TOCTOU race possible between the authorization check and mutation? Is a thundering herd risk addressed for cache-backed paths? | Time-of-check-to-time-of-use race on resource availability check; cache cleared on deploy causes thundering herd to the database |
| **Response Latency** | Are P95/P99 SLO targets defined and validated at expected concurrency? For fan-out to N services, is tail latency amplification modeled? | P99 undefined; fan-out to 5 downstream services at P99=60ms each — aggregate tail latency is substantially worse than per-service P99 |

**Additional Professional Considerations for Backend Code:**
- **GC pressure**: In JVM/Node.js/.NET runtimes, high per-request object allocation causes GC pause spikes that appear as P99 spikes only under load — invisible in local dev testing. Profile allocation rate per endpoint before accepting bulk-processing code.
- **Connection pool exhaustion — Little's Law**: Required pool size ≥ (target RPS) × (average service time in seconds). The default pool size (e.g., `pool: 10`) is almost never correct for production workloads. Validate with measurement, not assumption.
- **Back-pressure design**: Bounded queues with back-pressure are preferred over unbounded queues (OOM) or no queues (immediate rejection storms). Design the degradation mode explicitly.
- **Deferred optimization threshold**: If the current approach is acceptable only below a data volume or RPS threshold, document that threshold explicitly with a named owner — do not leave it as an undocumented time bomb.
- **Cognitive complexity**: Functions > 25 cognitive complexity must be decomposed before handoff. Clever code with a 3% CPU gain that requires 45 minutes to understand is not a net win.
