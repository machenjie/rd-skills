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

# Stage Fit

- **Planning / design:** define latency, throughput, payload, bundle, query, memory, CPU, capacity, and unit-cost budgets before implementation locks in scale shape.
- **Coding / implementation:** update endpoints, routes, jobs, workers, queries, dependency fan-out, bundle splits, resource limits, and enforcement hooks together with the changed path.
- **Bug-fix / debugging / repair:** reproduce failed budget, SLO burn, bill spike, load-test miss, bundle growth, query scan, RSS growth, or queue saturation before changing thresholds or code.
- **Code-review / refactoring:** reject performance claims that lack current-source inspection, baseline freshness, changed-path-to-budget mapping, enforcement evidence, and behavior preservation for existing gates.
- **Testing / release / handoff:** verify CI/load/canary/query/bundle/cost evidence, exception owner/expiry, rollback threshold, residual not-verified limits, and reliability/release handoff before promotion.

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

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New production surface budget | New API, route, job, worker, query, dependency fan-out, batch, or resource-intensive feature. | Define user-impact, throughput, resource, and cost ceilings before implementation locks in scale shape. | Baseline or industry anchor, expected data volume/concurrency, blocking threshold, and enforcement gate. | `solution-optimality-evaluation`, `algorithm-data-structure-selection`, `quality-test-gate` | Micro-optimization or profiler work before a budget exists. |
| Existing budget evolution | Threshold, budget scope, device profile, load scenario, or exception changes. | Preserve old behavior while recalibrating from current telemetry or business/SLO requirement. | Old/new threshold, baseline freshness, exception owner, expiry, and affected validation. | `observability`, `delivery-release-gate`, `reliability-observability-gate` | Lowering a gate only because CI is failing. |
| Performance-sensitive implementation review | Code path changes allocation, fan-out, payload, query count, bundle size, worker concurrency, or long-running process memory. | Map changed paths to budget dimensions and reject unbounded growth. | Changed-path-to-budget map, runtime/algorithm bounds, validator command, evidence limits. | `language-performance-safety`, `concurrency-control`, `profiling` | Claiming "small change" without input-size or path-frequency evidence. |
| Cost and capacity budget | Cloud resource, warehouse scan, egress, storage lifecycle, autoscaling, queue depth, or per-tenant cost changes. | Express spend as unit economics and connect it to capacity and anomaly gates. | Cost per request/tenant/job/query scan, approved ceiling, owner, anomaly threshold. | `reliability-observability-gate`, `bigdata-product-extension`, `delivery-release-gate` | Monthly total without unit driver. |
| Release enforcement and exception | CI/load/canary budget violation, launch exception, or post-incident budget hardening. | Decide block/warn/exception, preserve evidence freshness, and define rollback or revisit threshold. | Command output, canary/load result, exception owner/expiry, rollback threshold. | `quality-test-gate`, `delivery-release-gate`, `agent-execution-discipline` | Green release claim without current validator output. |

# Industry Benchmarks

Anchor against Google Core Web Vitals and RAIL for browser/user-perceived latency; Lighthouse CI, bundlesize, k6, Gatling, and Playwright performance assertions for enforcement; SRE latency-budget and error-budget practice for production-facing thresholds; Little's Law, Amdahl's Law, USE/RED methods, and runtime profiler guidance for capacity, pool, and saturation reasoning; EXPLAIN/ANALYZE and query-plan evidence for database work; and FinOps unit economics for request, tenant, job, scan, storage, autoscaling, and egress costs. Keep this body focused on selection, evidence, output, and quality gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed budget matrices, enforcement templates, decision trees, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when the primary concern is **defining and enforcing measurable performance or cloud cost thresholds** before a change ships. Route here for latency budget, throughput budget, memory budget, cloud cost budget, query scan budget, and per-feature cost ceiling. Route elsewhere when: **profiling** is primary (diagnosing an existing production regression or cost anomaly); **observability** is primary (SLI/SLO alert definitions and error budgets for operational monitoring); **indexing-query-optimization** is primary (tuning a specific slow query's execution plan); **degradation-circuit-breaking** is primary (defining fallback behavior when performance degrades beyond threshold).

# Risk Escalation Rules

Escalate when: a change removes or changes an existing budget threshold without a documented justification and updated baseline measurement; a load test reveals that the P99 budget is exceeded at less than 50% of expected peak concurrent users; a database query change results in a seq scan on a table with > 100K rows in production; a frontend bundle size increase exceeds 20% of the current budget without lazy-loading justification; memory RSS grows > 50% above baseline after 12 hours of steady-state load (potential leak); or projected cloud unit cost, query scan cost, egress, or storage growth exceeds the approved per-feature cost ceiling.

# Proactive Professional Triggers

- **Signal:** a change adds an endpoint, route, job, worker, query, external call, or batch path with no P95/P99, throughput, payload, memory, or unit-cost threshold.
  **Hidden risk:** regressions are subjective until users, SLO burn, queue backlog, or bills reveal missing budget ownership.
  **Required professional action:** require and document mode, budget dimensions, baseline source, blocking threshold, and enforcement gate before handoff.
  **Route to:** `performance-budgeting`, `quality-test-gate`.
  **Evidence required:** baseline or industry anchor, expected load/data volume, threshold matrix, command/canary gate, and residual not-verified scope.
- **Signal:** budget numbers come from project memory, prior reports, or repository graph without current source or telemetry confirmation.
  **Hidden risk:** stale baselines under-budget or over-budget the wrong route, query, job, traffic shape, pricing tier, or release gate.
  **Required professional action:** inspect and verify current route/query/job/source ownership, telemetry window, pricing driver, and validation freshness or disclose not-verified limits.
  **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`.
  **Evidence required:** inspected paths, accepted/rejected memory, telemetry/report timestamp, freshness limit, and residual unknowns.
- **Signal:** implementation uses nested scans, load-all, unbounded fan-out, large batch, broad `Promise.all`, or growing cache while the budget only names latency.
  **Hidden risk:** memory, CPU, pool, fan-out, retry, and cost failure modes remain uncapped even if a small test passes.
  **Required professional action:** require algorithm/runtime bounds, compare input-size assumptions, and map every growth surface to a budget and validator.
  **Route to:** `algorithm-data-structure-selection`, `language-performance-safety`, `concurrency-control`.
  **Evidence required:** input size, complexity, memory/item cap, pool/fan-out ceiling, benchmark/profile plan, and residual saturation risk.
- **Signal:** a frontend budget is total bundle only or measured on a fast developer machine.
  **Hidden risk:** route-specific users pay for unused code and median devices silently miss Core Web Vitals.
  **Required professional action:** require route/chunk budgets, representative device/network profile, and exception owner before treating the frontend budget as valid.
  **Route to:** `frontend-testing`, `frontend-change-builder`.
  **Evidence required:** Lighthouse/device profile, per-route chunk delta, CWV thresholds, report path, and exception owner/expiry.
- **Signal:** database or warehouse budget lacks production-scale data volume, plan/scan evidence, or rows examined/returned limit.
  **Hidden risk:** dev-data timing hides full scans, N+1 fan-out, stale statistics, and query-scan cost until production load.
  **Required professional action:** inspect representative plan, require scan budget, document data volume, and hand off query repair when the plan is not acceptable.
  **Route to:** `indexing-query-optimization`, `data-middleware-change-builder`.
  **Evidence required:** query scope, data volume, EXPLAIN/scan bytes, rows examined/returned, validator output, and validation gap.
- **Signal:** cost budget is a monthly total with no per-request, tenant, job, query, storage, egress, or autoscaling driver.
  **Hidden risk:** launch scales cost nonlinearly and invoice evidence arrives too late for rollback.
  **Required professional action:** express cost as unit economics, classify the driver, set anomaly thresholds, and document rollback or revisit condition.
  **Route to:** `reliability-observability-gate`, `delivery-release-gate`.
  **Evidence required:** unit driver, ceiling owner, anomaly threshold, billing/export report, rollback/revisit condition, and residual cost risk.
- **Signal:** CI/load/canary validation predates the final edit or covers only a smoke path while claiming budget readiness.
  **Hidden risk:** stale evidence closes the gate for untested code, changed paths, device profiles, or cost drivers.
  **Required professional action:** rerun, mark stale, or block; map every material changed path to a validator and preserve what the evidence cannot prove.
  **Route to:** `validation-broker`, `agent-execution-discipline`, `quality-test-gate`.
  **Evidence required:** changed path, validator, outcome, freshness timestamp, artifact/report path, and residual risk owner.

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

- **Missing latency budget:** change ships without a latency budget; P99 in production is 2.4 seconds; three months of incident reports reference "slow checkout" before the regression is identified as the change.
- **Underpowered load test:** load test runs at 10 VU; production peak is 800 VU; P95 at 10 VU is 120ms; at 800 VU it is 1.8 seconds; database connection pool exhaustion not discovered until production traffic spike.
- **Route bundle creep:** frontend bundle grows from 180 KB to 420 KB over 6 feature releases; no per-chunk budget enforcement; LCP degrades from 1.8s to 4.2s on 4G; user conversion drops 12%.
- **Batch-window collision:** background job defined without wall-clock budget; data volume doubles; job runs 8 hours and overlaps with business hours; API P99 degrades as database CPU is dominated by the batch job.
- **Unbounded RSS growth:** memory leak in Node.js worker grows RSS 50 MB per hour; no memory budget or monitoring; OOM kill occurs every 18 hours; restarts cause 30-second availability gaps.
- **Cold-start blind spot:** Kubernetes pod cold start takes 8 seconds; during a rollout, 15% of requests hit cold pods; P99 spikes to 9 seconds; rollout not automatically blocked.
- **Unit-cost surprise:** monthly budget looked safe, but per-tenant query scans and cross-region egress scale nonlinearly after launch; rollback happens after invoice close instead of at anomaly threshold.
- **Stale validation closure:** load test passed before the final dependency fan-out edit; release proceeds with green evidence that never exercised the shipped path.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 routing, budget dimensions, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete budget, exception, release gate, or changed-path-to-budget map. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark thresholds, budget selection matrices, enforcement templates, cost/capacity patterns, or graph/memory/trajectory coupling are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure registry routing or metadata-only edits where no performance, cost, or resource budget is being produced.

# Output Contract

Return a performance budget specification with:

- `mode_selected` (new production surface, existing budget evolution, implementation review, cost/capacity budget, or release enforcement/exception)
- `boundaries_inspected` (source paths, API/route/job/query/worker/dependency surfaces, existing budgets, tests, CI gates, dashboards, release checks, and prior memory accepted or rejected)
- `source_evidence` (current source, repository graph, project memory, execution trajectory, telemetry, load result, query plan, bundle report, or billing data inspected with freshness limits)
- `budget_scope` (which change surfaces are budgeted: API endpoints, frontend routes, queries, jobs, background workers)
- `latency_budgets` (per endpoint/flow: P50/P95/P99/P999 targets; percentile justification; baseline measurement or industry anchor)
- `frontend_budgets` (LCP, INP, CLS, TTI; device profile; measurement tool; Lighthouse CI configuration)
- `bundle_budgets` (per chunk: `main.js`, vendor chunks, per-route lazy-loaded chunks; gzipped KB limit; enforcement tool)
- `query_budgets` (per query: max execution time at production data volume; rows examined/returned ratio; index requirement; EXPLAIN validation requirement)
- `cloud_cost_budgets` (cost per request, cost per tenant, cost per job, query scan budget, storage lifecycle cost, egress budget, autoscaling cost impact)
- `per_feature_cost_ceiling` (approved spend ceiling, owner, approval gate, and cost anomaly threshold)
- `job_budgets` (per job/pipeline: wall-clock window; CPU and memory peak limits; concurrency impact on API latency)
- `memory_budgets` (baseline RSS; maximum RSS after 24h load; heap growth between GC cycles; container limit recommendation)
- `capacity_and_concurrency_budgets` (Little's-Law pool sizing, worker/fan-out limits, queue/backlog bounds, cold/warm path distinction)
- `enforcement_gates` (CI/CD integration: Lighthouse CI config, k6/Gatling threshold assertions, bundlesize config, EXPLAIN validation script)
- `load_test_scenario` (concurrency levels: average load, expected peak, spike; ramp-up profile; VU targets)
- `measurement_baseline` (source of baseline numbers: production P-tile measurements, load test results, or justified industry anchors)
- `escalation_thresholds` (conditions for blocking release: which budget violations block vs warn)
- `changed_path_to_budget_map` (each changed endpoint, route, query, job, bundle, dependency, runtime growth surface, or cost driver mapped to budget and validator)
- `reuse_and_placement_rationale` (existing budgets, profiles, dashboards, tests, and release gates reused; rejected speculative new tooling)
- `behavior_preservation` (old budget thresholds, old routes/jobs/queries, existing SLO promises, dashboards, and release gates preserved or intentionally changed)
- `validation_evidence` (commands, reports, load/canary/query/bundle artifacts, exit codes, freshness, or not-verified disclosure)
- `handoff_boundaries` (profiling, observability, query optimization, degradation, runtime safety, release, or security work that belongs elsewhere)
- `evidence_limits` (what the budget proves and does not prove about production load, data skew, browser/device mix, cloud pricing, tail latency, and release readiness)

# Evidence Contract

Close a performance budget only when these answers are concrete:

- **Budget basis:** selected mode, user/operational scenario, baseline source, business/SLO/industry anchor, and why each number is a threshold rather than a guess.
- **Current boundaries inspected:** source paths, routes, jobs, queries, frontend chunks, workers, dependencies, existing budgets, dashboards, validators, registry/project memory, and execution trajectory checked or explicitly not found.
- **Scale and cost proof:** expected and peak load, data volume, concurrency, memory/item bounds, pool/fan-out sizing, payload/bundle size, query scan, and unit-cost driver named with freshness limits.
- **Enforcement proof:** each changed path maps to CI/load/canary/query/bundle/cost validator, exit status or not-run disclosure, what evidence proves, and what it does not prove.
- **Behavior preservation:** old thresholds, performance promises, release gates, and monitoring remain valid or the intentional change and approval owner are named.
- **Handoff and residual risk:** profiling, observability, degradation, query tuning, runtime safety, release, security, or product owner handoff is named when the budget cannot prove readiness alone.

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
13. Current-source, graph, memory, or telemetry evidence is freshness-scoped; stale or inferred baselines are marked not verified.
14. Every material changed endpoint, route, query, job, bundle, dependency, runtime growth surface, or cost driver maps to a budget and validator or to named residual risk.
15. Algorithm, runtime, concurrency, and capacity assumptions include input size, memory bound, pool/fan-out ceiling, or explicit handoff.
16. Validation evidence is fresh after the final material edit and does not report smoke, lint, or one-path checks as full budget proof.

# Used By

- reliability-observability-gate
- frontend-change-builder

# Handoff

Hand off to `profiling` for performance regression diagnosis in production; `observability` for SLI/SLO alert configuration based on the defined budgets; `indexing-query-optimization` for query execution plan tuning; `degradation-circuit-breaking` for fallback behavior design when latency budgets are exceeded.

# Completion Criteria

The capability is complete when **every production-facing surface in the change has an explicit, measurable, percentile-specified performance budget and, where material, a cloud cost budget that is enforced automatically in CI/CD or release gates, validated at production data volume and peak concurrency, and linked to an escalation path when the budget is exceeded**.
