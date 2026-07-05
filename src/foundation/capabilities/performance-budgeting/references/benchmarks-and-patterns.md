# Performance Budgeting Benchmarks And Patterns

Use this reference when `performance-budgeting` needs more depth than the main `SKILL.md` can carry efficiently. Keep the main body focused on routing, evidence, output, and gates; use this file for budget threshold anchors, enforcement examples, decision matrices, capacity/cost patterns, and anti-pattern review.

## Benchmark Anchors

- **Core Web Vitals and RAIL:** LCP, INP, CLS, TTI, response, animation, idle, and load thresholds for browser/user-perceived performance.
- **Google SRE practice:** latency budgets, error-budget policy, symptom-based alerting, capacity planning, and release-blocking gates.
- **Lighthouse CI, bundlesize, Playwright, k6, Gatling, JMeter:** automated budget checks for frontend, bundle, browser interaction, API, and load scenarios.
- **USE and RED methods:** resource utilization/saturation/errors and service rate/errors/duration for capacity and runtime budget dimensions.
- **Little's Law:** in-flight work, pool size, worker count, and queue depth derived from throughput multiplied by service time.
- **Amdahl's Law and Universal Scalability Law:** parallelism and contention ceilings for worker, fan-out, and batch designs.
- **EXPLAIN/ANALYZE and query telemetry:** rows examined, rows returned, buffers, scan type, query duration, and warehouse scan bytes.
- **Runtime profilers and GC logs:** allocation rate, RSS, heap growth, GC pause, event-loop lag, lock contention, and pool saturation.
- **FinOps unit economics:** cost per request, tenant, job, query scan, storage GB-month, egress GB, and autoscaling unit.
- **OpenTelemetry and billing exports:** trace/span attribution, resource usage, and cost driver evidence joined to product paths.

## Budget Dimension Matrix

| Budget dimension | Strong starting point | Evidence required | Escalate when |
| --- | --- | --- | --- |
| API latency | P95 for standard paths, P99/P999 for critical or SLA-bound paths. | Baseline percentile, load scenario, endpoint/flow scope. | Fan-out, retries, or dependency P99 dominates end-to-end latency. |
| Throughput | Target RPS/QPS/TPS at average, peak, and spike load. | Traffic forecast, current capacity, saturation point. | Budget fails below expected peak or queue grows faster than drain rate. |
| Frontend vitals | LCP <= 2.5s, INP <= 200ms, CLS <= 0.1, route TTI threshold. | Lighthouse/field data, device/network profile, route scope. | Median-device or field data misses budget while dev machine passes. |
| Bundle and payload | Per-route/chunk gzip limit, API response/page size, image budget. | Bundle report, payload sample, compression status. | Total-only budget hides large route or vendor regression. |
| Query and scan | Execution time, rows examined/returned, index use, scan bytes. | Representative data volume and plan/scan output. | Dev data, stale stats, or full table/partition scan is the only evidence. |
| Memory and allocation | Startup RSS, steady-state RSS, allocation rate, heap growth after soak. | Load/soak result, profiler/GC log, container limit. | Unbounded input or cache grows with tenants, payload, messages, or retries. |
| CPU and worker capacity | CPU utilization ceiling, pool/worker count, event-loop lag, queue bound. | Little's-Law sizing, saturation metric, concurrency profile. | Pool defaults, unbounded fan-out, or lock contention decide capacity. |
| Batch and job window | Wall-clock completion, records/sec, checkpoint interval, API impact. | Representative input volume, shared-resource impact, retry/restart plan. | Job overlaps business hours or degrades user-facing P99. |
| Cloud unit cost | Cost per request, tenant, job, query scan, egress, storage lifecycle. | Billing/export driver, forecast, approved ceiling. | Spend scales nonlinearly with fan-out, retries, scan volume, or egress. |

## Budget Selection Decision Tree

```
What surface can regress?

User-facing API or service flow
  -> Set P95/P99 latency and throughput budgets.
  -> Include dependency fan-out and retry budget.
  -> Enforce with load/canary gate at average, peak, and spike load.

Frontend route or interaction
  -> Set LCP, INP, CLS, TTI, long-task, and per-route bundle budgets.
  -> Measure on representative slow device/network profile.
  -> Enforce in Lighthouse CI, browser perf tests, or field-data gate.

Database or warehouse path
  -> Set execution time, rows examined/returned, scan bytes, and index requirement.
  -> Validate with representative data and current schema/statistics.
  -> Hand off to indexing-query-optimization when plan repair is needed.

Background job, worker, or pipeline
  -> Set wall-clock window, throughput, checkpoint/retry budget, CPU, RSS, queue depth.
  -> Prove it does not degrade concurrent user-facing P99 or shared resource saturation.
  -> Include cold-start/restart budget if workers are ephemeral.

Runtime growth surface
  -> Set collection/cache/batch/fan-out/retry/pool item or byte ceiling.
  -> Reject or stream/chunk oversized inputs before allocation.
  -> Hand off to language-performance-safety or concurrency-control when lifecycle or lock risk dominates.

Cloud resource or cost driver
  -> Set unit cost and capacity ceiling by request, tenant, job, query, storage, egress.
  -> Define anomaly threshold and rollback/kill-switch condition.
  -> Tie spend to the rollout, feature flag, tenant cohort, or workload.
```

## Enforcement Templates

Use templates as examples, not fixed mandates. Values must be calibrated to baseline, business requirements, and production-like load.

```yaml
# Lighthouse CI concept
budgets:
  - path: "/*"
    timings:
      - metric: largest-contentful-paint
        budget: 2500
      - metric: interactive
        budget: 3800
      - metric: cumulative-layout-shift
        budget: 0.1
    resourceSizes:
      - resourceType: script
        budget: 300
      - resourceType: total
        budget: 800

# k6/Gatling concept
thresholds:
  http_req_duration:
    - "p(95)<500"
    - "p(99)<1000"
  http_req_failed:
    - "rate<0.01"

# bundle budget concept
bundlesize:
  - path: "./dist/main.*.js"
    maxSize: "150 kB"
  - path: "./dist/vendor.*.js"
    maxSize: "200 kB"
  - path: "./dist/route-admin.*.js"
    maxSize: "50 kB"
```

## Capacity And Pool Budget Patterns

Little's Law converts traffic and latency into in-flight work:

```
in_flight = peak_throughput_per_second * service_time_seconds
pool_size = in_flight * safety_factor
```

Use it for DB pools, HTTP client pools, worker pools, queue consumers, and outbound fan-out ceilings. Then validate with pool wait time, queue depth, saturation, and tail latency. Defaults are rarely evidence: a DB pool of 10 may be too small for 500 RPS at 50 ms average query time, and too large for a database with tight connection limits.

Budget checklist:

- name the pool, queue, or worker scope;
- state average and peak arrival rate;
- state P50/P95/P99 service time;
- calculate expected in-flight work;
- set bounded queue/fan-out/concurrency limit;
- define rejection, backpressure, or shedding behavior;
- add saturation metric and alert threshold;
- include cleanup/shutdown behavior for long-lived clients and pools.

## Graph, Memory, And Trajectory Coupling

Performance budgets often rely on historical knowledge. Treat that knowledge as a hint until source-confirmed.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current call sites, route ownership, jobs, queries, and dependencies are inspected. | Graph proximity is used as proof of hot path without source or telemetry. |
| Project memory | Baseline, incident, or prior budget has timestamp, owner, and unchanged path. | Memory predates major schema, route, deployment, traffic, or pricing change. |
| Execution trajectory | Recent validator/build/load output is after final material edit. | Output is stale, partial, or from a different path/environment. |
| Telemetry/dashboard | Query/load/field data source, time window, and environment are named. | Dashboard metric lacks route/path labels or includes high-cardinality/unbounded labels. |
| Billing export | Cost is attributed to request, tenant, job, scan, storage, or egress driver. | Only monthly aggregate spend is available. |

Strong handoffs say which hints were accepted, which were rejected, and what remains unknown.

## Evidence Patterns

- New endpoint: route source inspected, traffic forecast named, P95/P99 budget set, load test threshold added, query/payload/fan-out limits mapped, stale evidence disclosed.
- Frontend route: route chunk delta and CWV budget tied to device/network profile, unused vendor growth rejected, Lighthouse/bundle command named.
- Query path: current SQL/ORM call site and representative plan inspected, rows examined/returned and scan cost budgeted, handoff to query optimization if the plan is not acceptable.
- Background job: record volume, restart/checkpoint behavior, wall-clock window, CPU/RSS ceiling, queue impact, and concurrent API P99 impact stated.
- Cost-sensitive launch: cost per tenant/request/job/scan and approved ceiling named, anomaly alert tied to rollout, rollback threshold documented.
- Exception: failing budget, owner, expiry, compensating control, release risk, and revisit validator named.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| "Fast enough" with no percentile, baseline, or enforcement. | Untestable; every release can claim success. |
| Mean latency budget. | Hides user-visible tail latency and fan-out amplification. |
| Total bundle budget only. | Route-specific users download unused code. |
| Dev-machine Lighthouse run as proof. | Median mobile CPU/network can miss the budget. |
| Query budget from small dev data. | Full scans and bad join orders appear only at production scale. |
| Monthly cloud budget only. | Unit-cost regressions are discovered after invoice close. |
| Existing project memory used as baseline without freshness check. | Historical baselines can become false after traffic, schema, or pricing changes. |
| Load test at average traffic only. | Peak and spike traffic reveal pool, lock, and saturation failure modes. |
| Budget exception without owner and expiry. | Temporary regressions become permanent policy drift. |
| Validation before final edit reported as proof. | Closure evidence does not cover the shipped content. |

## Handoff Boundaries

- Use `profiling` when the bottleneck is unknown or a failing budget needs diagnosis.
- Use `observability` when production SLI/SLO, dashboard, alert, or trace signal design is primary.
- Use `indexing-query-optimization` when a concrete SQL/ORM plan or index repair is needed.
- Use `degradation-circuit-breaking` when exceeding a budget requires timeout, fallback, circuit, or shed-load design.
- Use `language-performance-safety` when runtime allocation, GC, event-loop, pool, lock, or cleanup risk dominates.
- Use `concurrency-control` when contention, duplicate work, shared state, locks, or worker parallelism controls the budget.
- Use `delivery-release-gate` when canary, exception, rollout, rollback, or budget-blocking release policy is required.
