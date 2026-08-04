# Performance Budgeting Decision Patterns

Load this reference when current objectives and measurements leave competing threshold, workload, capacity, or enforcement choices. External benchmarks are comparison inputs, not product budgets.

| Surface | Budget shape | Required calibration |
| --- | --- | --- |
| User or API latency | Distribution and deadline by protected operation | Representative request mix, dependency path, load and error behavior |
| Throughput or concurrency | Sustained/burst work, queueing, accepted/rejected/degraded outcomes | Arrival and service distributions, pools, contention and downstream limits |
| Rendering or interaction | Named milestone on declared device/runtime/network state | User distribution or representative lab profile and content state |
| Payload or bundle | Transfer, parse/decode, execution and retained-memory cost by changed surface | Compression/cache/runtime behavior and target device or consumer |
| Query, scan, or storage | Plan/runtime, rows or bytes touched, query count and write amplification | Representative data volume, cardinality, skew, engine and cache state |
| Memory, CPU, or pools | Steady/peak use, allocation, occupancy, wait and leak/saturation signal | Warmup, runtime/collector mode, concurrency and soak or recovery shape |
| Job, queue, or pipeline | Completion, age/lag/depth, drain/replay and retry cost | Arrival/service shape, checkpointing and downstream recovery capacity |
| Unit cost | Cost per owned request, job, tenant, data, model, or product unit | Billing dimensions, cache/retry/egress/storage effects and growth scenario |

Use a queue or capacity model only as a hypothesis, then verify it against representative load and failure behavior. Set warning, blocking, abort, degradation, rollback, or exception behavior from the consequence of breach and the credibility of the measurement. Absolute ceilings and regression comparisons may coexist when each has separate authority.

Reject average-only success claims, unmatched before/after environments, tiny or uniform data presented as production capacity, and hidden rejected work. Also reject unbounded queues or fan-out, aggregate cost without unit attribution, silent exceptions, and optimization that changes correctness, security, or durability.

Proof scope: these patterns do not prove query plans, runtime bottlenecks, contention, degradation behavior, telemetry coverage, release authority, or production capacity. Require fresh evidence from the owning boundary before claiming those properties.
