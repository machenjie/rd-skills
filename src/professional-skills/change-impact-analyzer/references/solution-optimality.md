# Solution Optimality Self-Check — Change Impact Analyzer

Compiled from foundation capability `solution-optimality-evaluation`. Apply during blast
radius analysis to expose performance surface impacts that are not visible from
functional surface analysis alone. Loaded on demand per the skill's Reference Loading
Policy.

**Performance Surface Analysis — Four Questions for Every Change**

For each change being analyzed, explicitly answer these four questions ("N/A" requires a one-line rationale — not silence):

1. **Does this change add CPU to a hot path?** Does the new code execute on the critical user request path, a high-frequency background loop, or a frequently called internal service? If yes: what is the estimated CPU cost added per call, and what is the total CPU overhead at target RPS?

2. **Does this change increase memory consumption at scale?** Does the change add per-request allocations, grow in-memory state, increase batch sizes, or reduce eviction aggressiveness? If yes: what is the estimated memory growth per unit of load, and what is the effect at 2× current traffic?

3. **Does this change add network calls?** Does the change introduce new outbound HTTP calls, database queries, cache lookups, or message-queue publishes on a path that previously had none? If yes: how many calls per user action, and is there an N+1 fan-out pattern introduced?

4. **Does this change alter disk I/O patterns?** Does the change modify write frequency, log verbosity, index coverage, or storage engine access patterns? If yes: what is the I/O cost delta, and is it acceptable at production data volume?

**Performance Impact Classification Matrix** — add to the blast radius analysis:

| Performance Dimension | Impact Level | Evidence Required |
|---|---|---|
| CPU added to hot path | Direct / Indirect / None | Estimated cost per call × RPS = total CPU overhead |
| Memory growth at scale | Direct / Indirect / None | Growth per request or per data unit × expected volume |
| New network calls | Direct / Indirect / None | Call count per user action; N+1 risk assessment |
| Disk I/O pattern change | Direct / Indirect / None | Read/write delta; index coverage change |
| Lock contention change | Direct / Indirect / None | New shared state accessed; lock scope change |
| Throughput ceiling change | Direct / Indirect / None | Does the change lower the TPS ceiling of any downstream? |
| Response latency impact | Direct / Indirect / None | P99 latency budget of affected paths |

**Latent Performance Risks — Check These Before Declaring "No Performance Impact":**
- **Innocent-looking schema additions**: A new nullable column with a default does not rewrite the table, but a non-null column without a server-side default or a new index on a large table will. Always trace schema additions to their storage engine behavior.
- **Count increase in an existing N+1 pattern**: The change adds one new associated object type to an already-paginated list endpoint. An existing N+1 query that made N calls now makes 2N calls. The change did not introduce the N+1 — but it doubled its cost.
- **Background job frequency increase**: The change extends an existing background job with new work. The job was completing in 10 minutes. The new work adds 8 minutes. The job now runs 18 minutes and overlaps with the next scheduled run — creating queueing and resource contention.
- **Cache invalidation scope expansion**: The change invalidates a broader cache key pattern. What previously invalidated 1 cache entry now invalidates 50. On every relevant event, 50 cache entries expire simultaneously — thundering herd risk on every cache-invalidating action.
- **New synchronous dependency on SLO-critical path**: The change adds a synchronous call to a new service on a path that was previously self-contained. The calling service's availability is now coupled to the new dependency's availability (availability arithmetic: combined ≤ min(A_caller, A_callee)).
