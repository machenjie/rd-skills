---
name: profiling
description: Requires measurement before optimization and identifies CPU, memory, I/O, lock, query, network, rendering, and allocation bottlenecks with evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "66"
changeforge_version: 0.1.0
---

# Mission

**Locate the real performance bottleneck through systematic, evidence-based measurement before any optimization begins** — ensuring that CPU cycles, memory allocations, I/O waits, lock contention, query costs, network fan-out, and rendering work are diagnosed from representative production workloads, not from intuition, so that every optimization targets the actual constraint and can be validated by quantified before/after comparison.

# When To Use

Use this capability when: a production service, API endpoint, or background job is slower than its performance budget; a latency regression was introduced and the root cause is unknown; memory is growing unboundedly (potential leak) or GC pressure is degrading throughput; CPU utilization is elevated without a proportional increase in request rate; a query is taking > 200ms in production; cloud cost, query scan, egress, storage, or autoscaling spend spikes without a known driver; I/O waits, lock contention, or thread starvation is suspected; or a frontend page is failing Core Web Vitals (LCP, INP) and the JS execution budget is unknown.

# Do Not Use When

Do not use this capability to: justify speculative optimization of code that is not on any measured hot path ("this loop looks slow"); rewrite stable, correct code to a different algorithm without evidence that the current algorithm is the bottleneck; create microbenchmarks that do not represent production data volumes, concurrency levels, or workload shapes; or collect performance profiles that would capture sensitive user data, PII, or credentials in the profiling output.

# Stage Fit

- **Discovery / diagnosis** — define symptom, performance budget, affected path, and representative workload before naming the bottleneck.
- **Implementation / repair** — require a locked baseline and bottleneck classification before optimization code is changed.
- **Code review** — reject performance claims that lack a before/after measurement, artifact link, workload definition, or correctness guard.
- **Testing / release** — compare the same workload and profiling method after the fix, with privacy review and rollback trigger documented.

# Non-Negotiable Rules

- **Measure first; the hypothesis is only a starting point.** State a hypothesis ("I believe the bottleneck is database query latency") but collect objective measurement before optimizing. The bottleneck revealed by profiling frequently differs from the initial hypothesis (e.g., CPU is high but flame graph shows serialization overhead — not business logic). Optimizing the wrong layer wastes engineering time and may introduce new defects.
- **Workload must be representative: production data volume, production concurrency, and production query patterns.** A profiling run on a developer machine against 1,000 rows does not predict behavior at 50M rows. A single-threaded microbenchmark does not reveal lock contention visible at 200 concurrent requests. Profile with: the same data volume, the same concurrency (at minimum, representative concurrency), the same access patterns (hot data vs cold data). Use production load samples or anonymized production datasets — not developer fixtures.
- **Baseline must be captured before optimization.** The baseline must be: the same scenario (identical inputs, same data state, same concurrency); the same environment (staging that mirrors production, or a production shadow); the same profiling tool and measurement method. Without a locked baseline, "the optimization improved performance by 40%" is unverifiable.
- **Correctness must be preserved across every optimization step.** For each optimization: existing correctness tests must pass before and after. If optimization requires changing an algorithm (e.g., sorting strategy, aggregation approach), a behavior-equivalence test must be added. Optimizations that trade incorrect behavior for speed are defects, not improvements.
- **Profiling artifacts must not contain sensitive data.** Request bodies, SQL query parameters, user IDs, session tokens, payment card data, or any PII must not appear in profiling traces, heap dumps, flame graphs, or allocation profiles stored or shared outside production security boundaries. Use query normalization (PostgreSQL `pg_stat_statements` — normalized query text without parameter values), request ID sampling rather than full body capture, and heap snapshot filtering tools.
- **Identify the bottleneck category before proposing a fix.** Different bottleneck categories require different remediation strategies. Proposing "add a cache" for a problem that is actually lock contention will not fix the problem and adds complexity. Use the Bottleneck Classification Matrix before prescribing remediation.
- **Current graph, memory, and execution evidence must agree.** Repository paths, prior profiling notes, telemetry, benchmark output, and command history must be checked for freshness; stale memory is a lead, not proof.

# Industry Benchmarks

- **Systems Performance / USE method** for utilization, saturation, errors, CPU flame graphs, off-CPU waits, and Linux `perf`.
- **Google SRE** for distinguishing load-induced, dependency-induced, and code-induced resource collapse before tuning.
- **Runtime profilers** such as Java Flight Recorder / async-profiler, Go `pprof`, Python `py-spy`, Node/V8 CPU profiler, Clinic.js, and Chrome DevTools.
- **Data and query tools** such as `EXPLAIN ANALYZE`, MySQL JSON plans, `pg_stat_statements`, trace span counts, and warehouse dry-runs.
- **Load and cost tools** such as k6/JMeter, billing exports, autoscaling events, egress metrics, and per-request or per-tenant unit-cost breakdowns.

# Bottleneck Classification Matrix

| Bottleneck Class | Symptoms | Primary Tool | Common Root Cause | First Fix Candidate |
| --- | --- | --- | --- | --- |
| CPU-bound | High user CPU, flat I/O wait | Flame graph, `perf top` | Hot loop, regex, serialization, GC | Algorithmic improvement, reduce allocations |
| Memory / GC pressure | GC pauses, high allocation rate, heap growth | Heap snapshot, allocation profiler | Object churn, retained references, large collections | Reduce allocations per request, fix retention |
| I/O wait (disk) | High `iowait`, slow read/write ops | Off-CPU flame graph, `iostat` | Unbuffered writes, sequential scan, missing index | Buffered I/O, async writes, index |
| Lock contention | Thread starvation, p99 >> p50 at concurrency | Lock wait profile, thread dump | Shared mutable state, pessimistic lock scope | Reduce lock scope, optimistic locking, partitioning |
| Database query | Slow query log, high `db_query_duration` | EXPLAIN ANALYZE, `pg_stat_statements` | Sequential scan, N+1 queries, missing index | Index, query rewrite, N+1 fix via join or batch |
| Network fan-out | High external call count, long tail p99 | Distributed trace, span count | N+1 HTTP calls, chatty API, synchronous external waits | Batch calls, async fan-out, circuit breaker |
| Frontend rendering | Long Tasks > 50ms, poor INP/LCP | Chrome DevTools, Lighthouse | Large JS bundle, layout thrashing, sync work on main thread | Code splitting, debounce, off-main-thread work |
| Allocation / memory leak | Monotonic RSS growth, OOM after hours | Heap dump diff (before vs after) | Event listener accumulation, timer not cleared, global cache growth | Fix retention; clear listeners; bound cache size |
| Cloud cost / unit economics | Cost per request, tenant, or job rises faster than traffic | Billing export, usage metrics, trace spans, warehouse dry-run | Retry storm, full table scan, cross-region egress, over-scaling | Bound retries, partition query, cache, right-size scaling |

# Profiling Workflow

```
1. Symptom → Form Hypothesis
   "POST /orders P99 = 2.4s at 200 concurrent users"
   Hypothesis: "Database query is the bottleneck"

2. Reproduce Workload → Capture Baseline
   - Same data volume as production (or representative anonymized copy)
   - Concurrency: 200 VU (k6 / JMeter)
   - Profiling tool attached: async-profiler / py-spy / pprof
   - Baseline metrics locked: P50/P95/P99, CPU %, heap, GC pause rate

3. Collect Evidence → Identify Actual Bottleneck
   - CPU flame graph: where is CPU time spent?
   - Off-CPU flame graph: what is waiting (I/O, locks)?
   - EXPLAIN ANALYZE: is the query using the expected index?
   - Allocation profile: which allocation site dominates?
   - Trace spans: which span consumes the most elapsed time?

4. Classify Bottleneck → Select Remediation Strategy
   (Use Bottleneck Classification Matrix above)

5. Implement Fix → Verify Correctness
   - Run existing correctness tests (must pass)
   - Add behavior-equivalence test if algorithm changed

6. Re-profile → Compare Against Baseline
   - Same workload, same concurrency, same environment
   - Report: before P99, after P99, improvement %
   - Report: before CPU %, after CPU % (confirm no regression)

7. Document Results → Hand Off
   - Bottleneck classification, evidence, fix, before/after metrics
   - Residual risk (other bottlenecks that may emerge at higher load)
```

# Selection Rules

Select this capability when the primary need is to **identify where time, resources, or cloud spend are consumed** before an optimization is chosen. Route elsewhere when: **performance-budgeting** is primary (defining target latency or cost thresholds for a new feature); **indexing-query-optimization** is primary (tuning a specific query's execution plan after profiling confirms it is the bottleneck); **concurrency-control** is primary (designing locking strategy for a new data access pattern, not diagnosing contention in existing code); **observability** is primary (configuring ongoing production monitoring signals and SLO alerts, not diagnosing a specific regression).

# Proactive Professional Triggers

Use this capability proactively, even when the request does not ask for profiling:

- **Signal:** a change claims "faster", "optimized", "reduced cost", "lower memory", "lower latency", or "scales better" without a locked baseline. **Hidden risk:** the fix may target a cold path or change workload shape, making the performance claim unverifiable. **Required professional action:** require before/after measurements from the same workload before accepting the optimization. **Route to:** `profiling`, `performance-budgeting`, and `validation-broker`. **Evidence required:** baseline metric, workload definition, profiling artifact, after-measurement command, and residual risk.
- **Signal:** repository graph shows a new hot path, query, cache, worker, batch job, rendering path, fan-out, object pool, or concurrency primitive. **Hidden risk:** new resource consumption can shift the bottleneck to CPU, locks, memory, DB, network, or cloud spend without visible correctness failures. **Required professional action:** map the affected path to likely bottleneck classes and require representative measurement if the path is performance-sensitive. **Route to:** `repository-graph-analysis`, `language-performance-safety`, `concurrency-control`, and this capability. **Evidence required:** changed paths, caller/route/job graph, expected traffic/concurrency, and selected profiling tool.
- **Signal:** project memory, old benchmark notes, prior incident summaries, or generated reports are reused as performance proof. **Hidden risk:** stale memory can certify a bottleneck that disappeared, miss a new bottleneck, or reuse non-representative load data. **Required professional action:** compare memory with current telemetry, code paths, data volume, and execution trajectory before trusting it. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `observability`, and this capability. **Evidence required:** source date, accepted/rejected memory, current telemetry or command output, graph delta, and unknowns.
- **Signal:** a profiler, heap dump, trace, query plan, or billing export may include request bodies, SQL parameters, user IDs, tokens, payment data, tenant identifiers, or secrets. **Hidden risk:** profiling artifacts become sensitive data leaks or violate production access boundaries. **Required professional action:** define redaction, sampling, storage, and access policy before capture or sharing. **Route to:** `security-privacy-gate`, `agent-tool-permission-sandbox`, `secret-configuration-security`, and this capability. **Evidence required:** redaction rule, safe artifact location, sampling scope, access owner, and privacy review.
- **Signal:** the bottleneck points to a schema, index, API contract, external dependency, runtime, deployment, or rollback-sensitive fix. **Hidden risk:** a performance repair can break correctness, consumers, rollout safety, or production recovery. **Required professional action:** split profiling evidence from implementation approval and route to the exact specialist gate. **Route to:** `indexing-query-optimization`, `api-contract-design`, `delivery-release-gate`, `reliability-observability-gate`, and this capability. **Evidence required:** profile-to-fix map, affected boundary, validation command, rollback trigger, and handoff owner.

# Reference Loading Policy

- **L1:** Use only this `SKILL.md` for routing, rejecting speculative optimization, or requesting a missing baseline.
- **L2:** Load `references/checklist.md` when drafting or reviewing a real profiling plan, regression diagnosis, privacy-safe artifact capture, or before/after comparison.
- **L3:** Load `examples/example-output.md` when the output contract shape is unclear or a user-facing profiling report is required.
- **L4:** Pair with `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when bottleneck proof depends on changed paths, prior measurements, command output, telemetry, traces, or report freshness.
- **L5:** Pair with performance, reliability, security, data/API, delivery, or language/runtime gates only for the selected bottleneck class; do not load unrelated references for a simple missing-baseline rejection.

# Risk Escalation Rules

Escalate when: profiling is performed on a production system during business hours (risk of profiling overhead degrading live traffic — use off-peak, shadow traffic, or a representative staging environment); a heap dump or memory snapshot must be captured from a live production process (memory dump may expose in-flight sensitive data); the profiling investigation reveals a correctness defect in addition to a performance issue (stop and split); a cost anomaly points to unbounded retries, data exfiltration, cross-region egress, or a full table scan on regulated data; a proposed fix changes a public API contract, database schema, or integration boundary (requires separate change management); or a memory leak is confirmed and the process must be restarted to recover — notify operations before restart.

# Critical Details

- **Flame graph reading: wide bars are the bottleneck, not tall stacks.** In a CPU flame graph, the horizontal axis represents CPU time share. A wide bar means more CPU time is consumed by that function. A tall stack means many nested calls — but if the leaf functions are narrow, they are not expensive. Engineers unfamiliar with flame graphs frequently misread tall stacks as performance problems and wide leaf functions as acceptable.
- **N+1 query detection requires tracing, not just slow query log.** A query that takes 3ms each but is called 500 times per request contributes 1.5 seconds of latency invisible to slow query log (threshold typically 100ms). Detection requires distributed trace span count analysis (e.g., ORM-level query count per request) or database query count metrics per request.
- **GC tuning without reducing allocation rate is treating a symptom.** If heap profiling shows 500MB/sec allocation rate, increasing heap size or changing GC algorithm reduces GC pause frequency but does not reduce allocation pressure. Fix: identify the highest-volume allocation sites in the allocation flame graph and reduce object creation per request.
- **Production profiling overhead must be acceptable.** `async-profiler` CPU profiling: ~1% overhead at 100 Hz sampling (safe for production). `jmap` heap dump: pauses the JVM for the duration of the dump (seconds to minutes on large heaps — not safe during business hours). `py-spy`: sampling, no code changes, no overhead perceptible in most cases. `pprof` Go heap profile: 5% overhead by default. Document the overhead of the chosen profiling method before attaching to production.
- **Cost profiling joins billing and runtime evidence.** A billing export alone shows where money went; traces, query plans, autoscaling events, and retry metrics explain why. Attribute cost by request path, tenant, job, query, storage class, and egress path before proposing a cost fix.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "This loop looks slow, let me optimize it" — no measurement | Optimization may be on a cold path that runs 0.01% of requests; no impact | Profile first; optimize only confirmed hot paths |
| Microbenchmark on 100-row table: "query is fast, no index needed" | Production table has 20M rows; index missing; full table scan at 20M rows is 40s | Profile at production data volume; validate with EXPLAIN on production-scale data |
| Before/after measured on different request shapes | Baseline: search query with 10 results. After: search query with 2 results. "80% improvement" | Same inputs, same data state, same concurrency for before and after |
| Heap dump captured from production system during peak hours | JVM pause during heap dump; 30-second availability gap | Capture heap dump from standby replica or during off-peak window |
| Profiling output contains full SQL query with user ID parameter | `SELECT * FROM orders WHERE user_id = 12345 AND ...` in flame graph label | Use `pg_stat_statements` normalized query text; strip parameters from profiling output |
| "Add a cache" proposed before profiling confirms cache-miss cost | Bottleneck is actually a mutex lock; cache adds complexity without fixing the lock | Profile → classify bottleneck → cache is correct only if cache-miss latency is confirmed hot path |

# Failure Modes

- Optimization targets the wrong layer: CPU-level optimization implemented while distributed trace reveals 80% of latency is an external HTTP dependency with no timeout — P99 unchanged.
- Microbenchmark shows 3× improvement; production shows no improvement because the microbenchmark was not on the hot path at production concurrency.
- Memory leak diagnosed as "GC pressure" — heap size increased, GC tuned, service still OOMs every 6 hours because the leak is retained references in a static HashMap.
- N+1 query pattern generates 300 SQL queries per page render; slow query log threshold is 100ms; each query is 5ms; total = 1.5s latency; no slow query log entry; bottleneck invisible without trace-level query counting.
- Heap dump captured from primary database replica during peak load causes 45-second JVM pause; cascades to service timeout spike.
- Before/after comparison uses different concurrency levels: baseline at 50 VU, post-optimization at 20 VU; "60% improvement" is entirely explained by the 60% reduction in concurrency.

# Output Contract

Return a profiling report with:

- `symptom` (observed metric: P99 latency, CPU %, RSS growth, error rate, GC pause duration; with measurement source)
- `hypothesis` (initial bottleneck hypothesis; bottleneck class from matrix)
- `boundaries_inspected` (source paths, route/job/query/rendering surfaces, dependency calls, runtime, deploy target, dashboards, traces, and prior notes inspected)
- `workload_definition` (data volume, concurrency, access pattern; how representative of production)
- `baseline_metrics` (locked baseline: P50/P95/P99, CPU %, heap, GC rate; profiling tool and settings)
- `profiling_evidence` (flame graph description, EXPLAIN ANALYZE output, allocation profile top sites, trace span breakdown, or lock wait report)
- `graph_memory_execution_validation` (current repository graph, project memory, telemetry, command output, and profile artifacts accepted or rejected with freshness limits)
- `cost_profile` (when relevant: cost per request, cost per tenant, cost per job, query scan bytes, storage growth, egress path, autoscaling event, and billing metric source)
- `bottleneck_classification` (confirmed class from matrix: CPU-bound / memory / I/O / lock / query / network / rendering / leak)
- `root_cause` (specific code location, query, or pattern causing the bottleneck)
- `proposed_fix` (specific change; why it addresses the root cause)
- `profile_to_validation_map` (bottleneck evidence mapped to correctness tests, performance rerun, privacy check, rollout guard, and specialist handoff)
- `expected_impact` (quantified: "expect P99 to drop from 2.4s to < 500ms based on span showing query is 85% of elapsed time")
- `correctness_guards` (existing tests that must pass; new behavior-equivalence test if algorithm changes)
- `after_measurement_plan` (same workload, same concurrency, same profiling tool; acceptance threshold)
- `privacy_review` (confirms profiling artifacts do not contain PII, credentials, or sensitive fields)
- `evidence_limits` (what was not measured, non-representative data, profiler overhead, stale memory, or unavailable production telemetry)
- `residual_risks` (other bottlenecks that may surface after this fix; escalation conditions)

# Quality Gate

The profiling report is complete only when:

1. Baseline metrics are locked before any optimization is applied.
2. Bottleneck is identified with profiling evidence — not hypothesis alone.
3. Bottleneck classification from the matrix is stated.
4. Root cause is specific (function name, query, code location, or span).
5. Workload is representative of production (documented data volume and concurrency).
6. Proposed fix is matched to the identified bottleneck class.
7. Expected impact is quantified.
8. Correctness tests pass before and after the optimization.
9. After-measurement plan uses identical workload and profiling settings as baseline.
10. Profiling artifacts confirmed to contain no sensitive data.
11. Cost anomalies are attributed to a runtime driver and unit-cost dimension before optimization is proposed.
12. Repository graph and affected boundaries are inspected before selecting the profiling tool or fix owner.
13. Project memory, prior benchmarks, and incident notes are accepted or rejected with source dates and freshness limits.
14. Profile-to-validation map links each bottleneck claim to a correctness guard, rerun command, privacy check, and handoff gate.
15. Evidence limits and residual risk state what the profiling run proves, what it does not prove, and the next gate.

# Evidence Contract

The report must name `boundaries_inspected`, validation commands or artifacts, what evidence proves, what evidence does not prove, residual risk, and the next handoff gate. Profiling evidence proves only the measured workload, environment, data volume, and profiler settings; it does not prove unrelated paths, future traffic shapes, or correctness of the proposed fix without tests. If repository graph, project memory, telemetry, or rerun evidence is missing, return the smallest next measurement step instead of approving an optimization.

# Benchmark Coverage

External benchmark posts and tool defaults are screening aids only. Approval requires workload-shaped evidence from the target system or representative harness, plus before/after comparison under identical inputs, concurrency, environment, and artifact redaction policy.

# Routing Coverage

When selected by a router, report which adjacent capabilities were loaded or intentionally skipped: `performance-budgeting`, `language-performance-safety`, `observability`, `indexing-query-optimization`, `concurrency-control`, `security-privacy-gate`, `delivery-release-gate`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker`.

# Used By

- reliability-observability-gate
- data-middleware-change-builder

# Handoff

Hand off to `performance-budgeting` for formalizing the validated improvement as a budget threshold; `indexing-query-optimization` if profiling confirms a database query as the bottleneck; `concurrency-control` if profiling confirms lock contention as the bottleneck; `observability` for adding ongoing production monitoring signals based on confirmed bottleneck locations; `security-privacy-gate` if artifacts need sensitive-data handling; and `delivery-release-gate` if the fix changes rollout, capacity, or rollback behavior.

# Completion Criteria

The capability is complete when **the bottleneck is identified through objective profiling evidence at representative workload, the proposed fix is matched to the confirmed bottleneck class, the evidence is mapped to current graph/memory/execution signals, and the improvement is validated by before/after measurement under identical workload conditions with correctness preserved**.
