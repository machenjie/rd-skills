---
name: performance-budgeting
description: Defines latency, throughput, payload, bundle, memory, CPU, query, and resource budgets where performance risk can affect users or operations.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "65"
changeforge_version: 0.1.0
---

# Mission

**Define explicit, measurable performance and cost budgets** — latency, throughput, payload, bundle size, memory, CPU, query cost, cloud unit cost, and resource consumption — before a change ships, so that regressions are detected in CI/CD rather than discovered via user complaints, SLO burn, or cloud bill spikes, and so that architectural decisions (caching, indexing, pagination, code splitting, autoscaling) are driven by quantified requirements rather than intuition.

# When To Use

Use this capability when a change: introduces a new API endpoint, background job, or query that will run in production; adds or modifies a user-facing page where Core Web Vitals or interaction latency is measurable; increases payload sizes (response bodies, request bodies, bundle sizes, image assets) beyond a known threshold; changes a data access pattern (adds joins, removes index, changes query shape) in a system with > 1M records; adds a scheduled job or batch process without a documented execution time constraint; changes cloud resource usage, autoscaling behavior, query scan volume, storage growth, or egress; or follows a performance or cost incident where the root cause was an undefined or unenforced budget.

# Do Not Use When

Do not use this capability to: define SLI/SLO alert thresholds and operational error budgets (use `observability`); profile existing production code to diagnose a performance regression already in production (use `profiling`); tune database index selection or query execution plans for existing data (use `indexing-query-optimization`); or set arbitrary numbers without measurement data to justify them.

# Non-Negotiable Rules

- **Every performance budget must be justified by user impact data, business requirements, or measured baselines — not by guessing.** A budget of "< 200ms API latency" that has no baseline measurement and no user-impact justification is decoration. Acceptable justifications: industry benchmark (Google: < 200ms for perceived responsiveness); SLO derived from user research (checkout abandonment at > 3s); business requirement (partner SLA); measured baseline with regression threshold (current P99 = 180ms; budget = current + 20% headroom).
- **Performance budgets must be enforced in CI/CD — not documented in a wiki.** A budget that is only checked manually in occasional performance reviews is not a budget — it is a wish. Enforcement means: automated test that fails the build or merge when the budget is exceeded; or alerting in staging/canary that blocks promotion. Lighthouse CI, Jest performance assertions, k6/Gatling load test gates, and Playwright performance assertions are approved enforcement tools.
- **Latency budgets must be specified as percentiles, not means.** P50 (median) latency hides tail latency experienced by 50% of users. Budget specifications: P95 for standard API responses; P99 for critical user flows (checkout, auth, payment confirmation); P999 for financial settlement or SLA-bound partner APIs. Mean and max latency are diagnostic signals — not budget targets.
- **Frontend performance budgets must cover all three Core Web Vitals and TTI.** LCP (Largest Contentful Paint) ≤ 2.5s; INP (Interaction to Next Paint) ≤ 200ms; CLS (Cumulative Layout Shift) ≤ 0.1; TTI (Time to Interactive) ≤ 3.8s on a simulated 4G connection (Lighthouse default: 10 Mbps down, 40ms RTT, 4× CPU slowdown). Budget must be measured on a representative slow-device profile — not just the engineer's development machine.
- **Bundle size budgets must be enforced per route / per chunk, not only for total bundle.** A 500 KB JavaScript bundle that includes a charting library only used on the admin dashboard is unacceptable for users who never visit that dashboard. Budget: `main.js` ≤ 150 KB gzipped; per-route chunk ≤ 50 KB gzipped; third-party vendor chunk ≤ 200 KB gzipped (separate from application code). Webpack Bundle Analyzer / Rollup Visualizer / `bundlesize` tool must be used for enforcement.
- **Database query budgets must include both execution time and resource cost.** A query that runs in 50ms on 10,000 rows runs in 18 seconds on 10,000,000 rows with the same execution plan. Budget must specify: maximum execution time at expected data volume (measured, not estimated); maximum rows examined (EXPLAIN ANALYZE output); index requirement (query must use defined index — `seq scan` on large tables is a budget violation).
- **Cloud cost budgets must be specified as unit economics, not only monthly totals.** A monthly budget hides regressions until the invoice arrives. Define cost per request, tenant, batch job, query scan, storage GB-month, and egress GB for material changes; include an approved per-feature cost ceiling and a cost anomaly threshold.
- **Memory budgets must be specified for long-running processes.** A Node.js API server that starts at 200 MB RSS but grows to 2 GB RSS over 48 hours before OOM kill has a memory leak. Budget: baseline RSS at startup; maximum RSS after 24 hours of production load; maximum heap growth between GC cycles; container memory limit must be ≥ 2× maximum expected RSS (not tight).
- **Background job and batch process budgets must include wall-clock time, CPU, and memory peaks.** A nightly report job must complete within a defined window (e.g., must complete before business hours start at 06:00 local time); must not consume > X% CPU of shared processing capacity; must process N records within the window without degrading concurrent API latency.

# Industry Benchmarks

Anchor against: **Google Web Vitals (web.dev/vitals)** — Core Web Vitals standard: LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1; Good / Needs Improvement / Poor thresholds. **Lighthouse CI (github.com/GoogleChrome/lighthouse-ci)** — automated budget enforcement in CI; `lighthouserc.json` configuration with budget assertions. **RAIL Model (Response, Animation, Idle, Load)** — Response: < 100ms for interactions feeling instantaneous; Animation: 16ms per frame (60fps); Idle: < 50ms task chunks; Load: content displayed in < 1s (FCP). **HTTP Archive / Core Web Vitals Technology Report** — industry P75 baseline for LCP by framework; median JavaScript transfer size by sector. **Alex Russell "The Performance Inequality Gap"** — budget for median mobile device (Moto G Power, ~8× CPU slowdown vs MacBook); 200 KB total JavaScript parse budget on median mobile. **k6 / Gatling load testing** — `p(95) < 500` SLA assertion syntax; ramp scenarios (ramp-up, steady-state, spike, soak); virtual user (VU) targets. **EXPLAIN ANALYZE / Query Execution Plan** — `rows_examined` vs `rows_returned` ratio; `seq_scan` on > 10K rows without index = budget violation. **Container Resource Requests / Limits (Kubernetes)** — CPU request ≠ limit; memory limit OOM kill behavior; `resources.limits.memory` must not be set below peak RSS observed in load test. **Web Performance Budget Calculator (performancebudget.io)** — maps target load time to maximum transfer size by connection type.

### Performance Budget Reference Matrix

| Budget Type | Target Tier | Good | Needs Work | Poor / Reject |
| --- | --- | --- | --- | --- |
| API Latency P95 | Standard endpoint | < 200ms | 200–500ms | > 500ms |
| API Latency P99 | Critical flow (checkout, auth) | < 500ms | 500ms–1s | > 1s |
| LCP (Largest Contentful Paint) | Marketing / landing | ≤ 2.5s | 2.5–4.0s | > 4.0s |
| INP (Interaction to Next Paint) | Interactive app | ≤ 200ms | 200–500ms | > 500ms |
| CLS (Layout Shift) | Any page | ≤ 0.1 | 0.1–0.25 | > 0.25 |
| TTI (Time to Interactive) | App shell | ≤ 3.8s | 3.8–7.3s | > 7.3s |
| JS Bundle (main, gzipped) | SPA / PWA | ≤ 150 KB | 150–300 KB | > 300 KB |
| JSON Response Payload | API response | ≤ 50 KB | 50–200 KB | > 200 KB (paginate) |
| DB Query Execution Time | Standard read | < 50ms | 50–200ms | > 200ms → index or cache |
| Rows Examined / Row Returned | Query efficiency | ≤ 10× | 10–100× | > 100× → seq scan risk |
| Container Memory RSS | API server | ≤ container limit / 2 | 50–80% of limit | > 80% (OOM risk) |
| Cloud Unit Cost | Request / tenant / job | Within approved ceiling | 10-20% above baseline | > 20% above baseline or unbounded |
| Query Scan Budget | Warehouse / lake query | Partition-pruned and approved | Scans more than expected partition | Full scan without approval |

### Budget Enforcement Configuration Template

```yaml
# Lighthouse CI: lighthouserc.json
{
  "ci": {
    "assert": {
      "budgets": [
        {
          "path": "/*",
          "timings": [
            { "metric": "largest-contentful-paint", "budget": 2500 },
            { "metric": "interactive",               "budget": 3800 },
            { "metric": "cumulative-layout-shift",   "budget": 0.1 }
          ],
          "resourceSizes": [
            { "resourceType": "script",  "budget": 300 },
            { "resourceType": "total",   "budget": 800 }
          ]
        }
      ]
    }
  }
}

# k6 load test assertion (SLA gate)
thresholds:
  http_req_duration:
    - "p(95)<500"    # 95th percentile < 500ms
    - "p(99)<1000"   # 99th percentile < 1000ms
  http_req_failed:
    - "rate<0.01"    # error rate < 1%

# bundlesize (package.json)
"bundlesize": [
  { "path": "./dist/main.*.js",       "maxSize": "150 kB" },
  { "path": "./dist/vendor.*.js",     "maxSize": "200 kB" },
  { "path": "./dist/route-admin.*.js","maxSize": "50 kB"  }
]
```

### Performance Budget Selection Decision Tree

```
What type of performance risk does this change introduce?

API / Service Response Time?
  → Set P95 and P99 latency budgets
  → Add k6/Gatling load test gate at expected concurrent VU count
  → Add EXPLAIN ANALYZE budget (rows examined, index required)

Frontend Page Load / Interaction?
  → Set LCP, INP, CLS, TTI budgets via Lighthouse CI
  → Set per-chunk JS bundle size budgets via bundlesize
  → Measure on simulated slow-device profile (4G + 4× CPU)

Database Query / Data Access?
  → Set max execution time at expected data volume (not dev volume)
  → Require EXPLAIN output showing index usage (no seq scan on > 10K rows)
  → Set rows-examined / rows-returned ratio budget

Background Job / Batch Process?
  → Set wall-clock window (must complete before N:00 local time)
  → Set maximum CPU % consumed during window
  → Set maximum memory peak; validate does not degrade concurrent API P99

Memory Leak Risk (long-running process)?
  → Set baseline RSS + maximum RSS after 24h load test
  → Add heap growth metric (heap used before/after GC cycle)
  → Set container memory limit ≥ 2× expected peak RSS

Cloud Cost / FinOps Risk?
  → Set cloud cost budget per request, tenant, job, feature, and query scan
  → Set egress and storage lifecycle budgets
  → Add budget approval gate when projected spend exceeds threshold
  → Add cost anomaly alert tied to the rollout or feature flag
```

# Selection Rules

Select this capability when the primary concern is **defining and enforcing measurable performance or cloud cost thresholds** before a change ships. Route here for latency budget, throughput budget, memory budget, cloud cost budget, query scan budget, and per-feature cost ceiling. Route elsewhere when: **profiling** is primary (diagnosing an existing production regression or cost anomaly); **observability** is primary (SLI/SLO alert definitions and error budgets for operational monitoring); **indexing-query-optimization** is primary (tuning a specific slow query's execution plan); **degradation-circuit-breaking** is primary (defining fallback behavior when performance degrades beyond threshold).

# Risk Escalation Rules

Escalate when: a change removes or changes an existing budget threshold without a documented justification and updated baseline measurement; a load test reveals that the P99 budget is exceeded at less than 50% of expected peak concurrent users; a database query change results in a seq scan on a table with > 100K rows in production; a frontend bundle size increase exceeds 20% of the current budget without lazy-loading justification; memory RSS grows > 50% above baseline after 12 hours of steady-state load (potential leak); or projected cloud unit cost, query scan cost, egress, or storage growth exceeds the approved per-feature cost ceiling.

# Critical Details

- **Budget numbers must come from measurement, not industry defaults alone.** "We set 200ms because Google says so" is not sufficient without a measured baseline. P99 = 180ms baseline → budget = 220ms (20% headroom for regression detection). Industry benchmarks establish the floor; production measurement establishes the actual budget.
- **Load test at realistic concurrency, not just single-request latency.** A request that takes 50ms in isolation may take 800ms at 500 concurrent users due to connection pool exhaustion, lock contention, or cache miss amplification. Budget must be validated at expected peak concurrency (Black Friday level if applicable, not just average load).
- **Cold start vs warm cache budgets.** An API endpoint backed by a Redis cache responds in 15ms on cache hit and 350ms on cache miss. Budget must define both: cold path (cache miss / cold JVM / container cold start) and warm path (steady state). Alerting should fire on cold-path P95 exceeding budget during normal operation — which indicates cache eviction or a cold deployment.
- **Third-party dependency latency must be included in end-to-end budget.** If a payment confirmation API calls a fraud-check partner that P99s at 400ms, the end-to-end checkout confirmation budget must be ≥ 400ms + internal processing. Budgets that ignore third-party latency undercount the user-experienced time.
- **Unit cost baselines must use production-like volume.** Serverless, warehouse, CDN, queue, and object-storage pricing often has nonlinear thresholds. A feature that is cheap in a small test can become expensive when fan-out, retries, scan volume, or egress scales with tenants.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "Latency should be fast" — no number, no percentile, no enforcement | Untestable; every deployment passes by default | Set P95 < 300ms, P99 < 800ms; enforce in load test gate |
| Mean latency budget: "average response < 200ms" | Mean hides P99 = 2,000ms; 1% of users wait 10× longer | Budget on P95/P99; mean is a monitoring signal only |
| Lighthouse run on developer machine (M2 MacBook, Wi-Fi) | 4× faster than median mobile device; LCP 0.8s on dev = 2.4s on Moto G4 | Run Lighthouse CI with `--throttling-method devtools` simulating 4G + 4× CPU |
| Bundle budget: "< 1 MB total" | A 1 MB bundle on every route — user downloads 1 MB to view a static page | Per-route chunk budget ≤ 50 KB gzipped; lazy-load charts / admin modules |
| Query budget defined on 1,000-row dev database | EXPLAIN shows index scan on dev; seq scan on 10M-row prod; not discovered until production | Define budget at production data volume; validate EXPLAIN ANALYZE output against production-scale seed |
| Memory budget not set; container limit = 256 MB | Service grows to 240 MB after 6 hours; OOM kill at peak traffic | Set peak RSS budget from 24-hour load test; container limit = 2× peak RSS |

# Failure Modes

- Change ships without a latency budget; P99 in production is 2.4 seconds; three months of incident reports reference "slow checkout" before the regression is identified as the change.
- Load test runs at 10 VU; production peak is 800 VU; P95 at 10 VU is 120ms; at 800 VU it is 1.8 seconds; database connection pool exhaustion not discovered until production traffic spike.
- Frontend bundle grows from 180 KB to 420 KB over 6 feature releases — no per-chunk budget enforcement; LCP degrades from 1.8s to 4.2s on 4G; user conversion drops 12%.
- Background job defined without wall-clock budget; data volume doubles; job runs 8 hours and overlaps with business hours; API P99 degrades as database CPU is dominated by the batch job.
- Memory leak in Node.js worker: RSS grows 50 MB per hour; no memory budget or monitoring; OOM kill occurs every 18 hours; restarts cause 30-second availability gaps.
- Cold-start latency budget ignored: Kubernetes pod cold start takes 8 seconds; during a rollout, 15% of requests hit cold pods; P99 spikes to 9 seconds; rollout not automatically blocked.

# Output Contract

Return a performance budget specification with:

- `budget_scope` (which change surfaces are budgeted: API endpoints, frontend routes, queries, jobs, background workers)
- `latency_budgets` (per endpoint/flow: P50/P95/P99/P999 targets; percentile justification; baseline measurement or industry anchor)
- `frontend_budgets` (LCP, INP, CLS, TTI; device profile; measurement tool; Lighthouse CI configuration)
- `bundle_budgets` (per chunk: `main.js`, vendor chunks, per-route lazy-loaded chunks; gzipped KB limit; enforcement tool)
- `query_budgets` (per query: max execution time at production data volume; rows examined/returned ratio; index requirement; EXPLAIN validation requirement)
- `cloud_cost_budgets` (cost per request, cost per tenant, cost per job, query scan budget, storage lifecycle cost, egress budget, autoscaling cost impact)
- `per_feature_cost_ceiling` (approved spend ceiling, owner, approval gate, and cost anomaly threshold)
- `job_budgets` (per job/pipeline: wall-clock window; CPU and memory peak limits; concurrency impact on API latency)
- `memory_budgets` (baseline RSS; maximum RSS after 24h load; heap growth between GC cycles; container limit recommendation)
- `enforcement_gates` (CI/CD integration: Lighthouse CI config, k6/Gatling threshold assertions, bundlesize config, EXPLAIN validation script)
- `load_test_scenario` (concurrency levels: average load, expected peak, spike; ramp-up profile; VU targets)
- `measurement_baseline` (source of baseline numbers: production P-tile measurements, load test results, or justified industry anchors)
- `escalation_thresholds` (conditions for blocking release: which budget violations block vs warn)

# Quality Gate

The budget specification is complete only when:

1. Every budget number has a documented justification: measured baseline, SLO derivation, or named industry benchmark.
2. Latency budgets expressed as P95/P99 — not as mean or max.
3. Frontend budgets cover all four signals: LCP, INP, CLS, TTI — measured on simulated slow-device profile.
4. Bundle budgets are per-chunk, not only total.
5. Query budgets specify data volume at which they were validated.
6. All budgets have a CI/CD enforcement gate (Lighthouse CI, load test threshold, bundlesize config, or equivalent).
7. Load test covers both average load and peak concurrency — not single-user.
8. Memory budgets defined for all long-running processes (API servers, workers, daemons).
9. Cold-start and warm-path budgets specified separately for cached or JIT-compiled services.
10. Budget violations: distinction between blocking (release cannot proceed) and warning (investigation required).
11. Cloud cost budget exists for material resource changes, including query scan, egress, storage lifecycle, and per-feature cost ceiling.
12. Budget approval gate and cost anomaly alert are defined when projected spend can exceed the approved ceiling.

# Used By

- reliability-observability-gate
- frontend-change-builder

# Handoff

Hand off to `profiling` for performance regression diagnosis in production; `observability` for SLI/SLO alert configuration based on the defined budgets; `indexing-query-optimization` for query execution plan tuning; `degradation-circuit-breaking` for fallback behavior design when latency budgets are exceeded.

# Completion Criteria

The capability is complete when **every production-facing surface in the change has an explicit, measurable, percentile-specified performance budget and, where material, a cloud cost budget that is enforced automatically in CI/CD or release gates, validated at production data volume and peak concurrency, and linked to an escalation path when the budget is exceeded**.
