# Degradation Circuit Breaking Benchmarks And Patterns

Use this reference when `degradation-circuit-breaking` needs more depth than the main `SKILL.md` can carry efficiently. Keep the main body focused on routing, evidence, output, and quality gates; use this file for dependency classification, timeout/circuit/retry/bulkhead matrices, chaos-test patterns, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- **Release It! (Michael Nygard):** timeout, circuit breaker, bulkhead, fail-fast, and stability anti-patterns.
- **Google SRE Book and Workbook:** overload handling, load shedding, request hedging, backpressure, SLO burn, and error-budget policy.
- **Hystrix, Resilience4j, Polly, Sentinel:** in-process circuit breaker, retry, rate limit, bulkhead, fallback, and metrics patterns.
- **Envoy and Istio:** service-mesh circuit breaking, connection pools, outlier detection, and infrastructure-level ejection.
- **AWS exponential backoff and jitter:** full-jitter retry timing to avoid synchronized retry waves.
- **Toxiproxy, tc netem, AWS Fault Injection Simulator, LitmusChaos:** deterministic local, staging, and platform-level fault injection.
- **RFC 7807 / RFC 9457:** problem details for machine-readable degraded, timeout, and dependency-failure responses.
- **OWASP API Top 10 API4:** unrestricted resource consumption risk from unbounded calls, retries, and fan-out.

## Dependency Criticality Matrix

| Criticality | Definition | Failure policy | Examples | Escalate when |
| --- | --- | --- | --- | --- |
| CRITICAL-CLOSED | Required for correctness, authorization, money, or compliance. | Fail closed with safe error and immediate signal. | Auth, payment authorization, fraud, tenant isolation. | Anyone proposes fail-open or stale fallback. |
| CRITICAL-DEGRADABLE | Required for core flow but has a safe, explicit fallback. | Retry briefly, then typed degraded response; alert. | Price service with max-age cache, read replica fallback. | Fallback hides price, entitlement, or data-quality risk. |
| OPTIONAL-DEGRADABLE | Enhances experience; core flow can proceed without it. | Timeout aggressively, omit or degrade visibly, record metric. | Recommendations, personalization, search refinement. | Omission changes user promise or contractual output. |
| FIRE-AND-FORGET | Side effect not required for immediate user response. | Queue, retry, DLQ or drop only with approval and metric. | Analytics event, email notification, audit sink. | Loss is legal, audit, billing, or support relevant. |
| SOFT-REALTIME | Slow result hurts UX more than absent result. | Very short timeout, fall back to cached/default state. | Feature flag, A/B assignment, model inference. | Default can enable unsafe feature or disable core revenue path. |

## Timeout Budget Pattern

Start from the upstream request deadline and work backward.

```text
user_deadline = browser/client/user-facing SLO
api_budget = user_deadline - rendering/network margin
dependency_budget = api_budget - internal_processing_budget - safety_margin
```

Rules of thumb:

- User-facing connection timeout: 500 ms in the same VPC; 1-3 s across public internet.
- User-facing read timeout: dependency P99 * 2, capped below the upstream deadline and usually below 5 s.
- Background read timeout: dependency P99 * 3, capped by job deadline and retry budget.
- Downstream timeout must be shorter than upstream timeout with at least 20 percent buffer.
- Cancellation must propagate so timed-out calls release sockets, leases, locks, or worker slots.

Reject any timeout chosen only from a library default, sample code, or old memory without current source or telemetry confirmation.

## Circuit Breaker Matrix

| Parameter | Conservative | Standard | Aggressive | Choose by |
| --- | --- | --- | --- | --- |
| Failure threshold | 20 percent | 50 percent | 80 percent | Criticality and false-trip tolerance. |
| Minimum request volume | 5 | 10-20 | 50+ | Traffic volume and cold-start noise. |
| Sliding window | 10 calls or 30 s | 20-100 calls or 60 s | 100+ calls or 2-5 min | Traffic shape and recovery speed. |
| Open duration | 5-10 s | 30-60 s | 2-5 min | Provider recovery pattern and retry pressure. |
| Half-open probes | 1 | 3 | 5-10 | Probe cost and confidence required. |
| Close threshold | 1 success | 2-3 successes | sustained success window | Impact of reopening too early. |

State metrics:

- `circuit_state` with bounded labels: dependency, operation, state.
- `circuit_open_total`, `circuit_half_open_total`, `fallback_total`, `timeout_total`, `rejected_total`.
- Alert when a critical dependency circuit opens, or when fallback ratio burns the user-impact SLO.

## Retry Budget Pattern

Retry only when the operation is idempotent or protected by an idempotency key and dedupe store.

Retryable:

- HTTP 500, 502, 503, 504.
- HTTP 429 with bounded `Retry-After`.
- Network timeout, connection reset, DNS temporary failure.
- gRPC `UNAVAILABLE` and `RESOURCE_EXHAUSTED` when caller deadline permits.

Non-retryable:

- HTTP 400, 401, 403, 404, 409, 422 unless a documented reconciliation path says otherwise.
- Permission, validation, conflict, malformed payload, or idempotency mismatch.
- Unknown outcome mutation without idempotency key and reconciliation.

Backoff:

```text
sleep = random(0, min(cap, base * 2^attempt))
```

Budget:

- User-facing synchronous calls: usually 0-2 retries within the end-to-end deadline.
- Async/background work: more attempts allowed, but with deadline, DLQ, owner, and replay safety.
- Retry amplification target: additional retry load should be explicitly budgeted; stop retrying when the circuit is open.

## Bulkhead And Load-Shedding Pattern

Use a separate bounded resource for each risky dependency or operation class.

```text
in_flight = peak_rps * dependency_p99_seconds
pool_size = ceil(in_flight * safety_factor)
queue_size = bounded and justified, often 1x-2x pool_size
```

Controls:

- Thread or worker pool isolation for blocking dependencies.
- Semaphore isolation for async/non-blocking dependencies.
- Token bucket or leaky bucket for provider rate limits.
- Bounded fan-out for batch, search, model, and notification calls.
- Load shedding with a typed degraded response when queue/pool is full.

Metrics:

- pool active, waiting, rejected, queue depth, timeout, fallback, circuit state, and dependency error rate.

## Graph, Memory, And Trajectory Coupling

Treat historical knowledge as a hint until current evidence confirms it.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current call sites, owners, dependency clients, queues, and fallbacks are inspected. | Graph proximity is used as proof of optionality or protection without reading source. |
| Project memory | Prior incident, fallback, SLO, or provider behavior has timestamp, owner, and unchanged path. | Memory predates traffic, dependency, SDK, topology, tenancy, or product criticality change. |
| Execution trajectory | Validation, chaos, load, or incident evidence is after the final material edit. | Evidence is stale, partial, or from a different dependency/environment. |
| Telemetry | Dashboard/query names dependency, operation, environment, and time window. | Metrics have unbounded labels, no route/operation split, or only infrastructure health. |
| Runbook | Owner, rollback/disable path, and recovery criterion are current. | Runbook is untested or points at removed dashboards/tools. |

Strong handoffs say which graph/memory/trajectory inputs were accepted, which were rejected, and what remains not verified.

## Resilience Evidence Patterns

- **New dependency:** source call site inspected, criticality classified, timeout and retry budget set, circuit metrics named, fallback test required.
- **Existing dependency change:** old and new timeout/retry/circuit defaults compared, SLO impact and validation freshness stated.
- **Fallback design:** typed degraded state, product approval, user impact, stale age, alert threshold, and test path named.
- **Retry storm repair:** baseline error/retry/fallback rates captured, cause verified, circuit or retry budget changed, before/after fault test run.
- **Bulkhead design:** pool/fan-out/queue bound calculated with Little's Law, reject behavior and saturation metrics defined.
- **Kill switch:** typed config, safe default, owner, rollback path, telemetry, cleanup condition, and release gate named.
- **Exception:** untested chaos path or missing provider telemetry is owned, time-boxed, and tied to rollback/watch criteria.

## Anti-Patterns To Reject

| Anti-pattern | Why it fails |
| --- | --- |
| No timeout on an HTTP/gRPC/SDK client. | A slow dependency can consume all request and pool capacity. |
| Retry on non-idempotent POST without idempotency key. | A transient failure can create duplicate charges, orders, or writes. |
| Circuit breaker at library default. | Defaults often mismatch traffic and criticality, causing false trips or no protection. |
| Auth/payment/fraud/compliance fail-open. | Availability incident becomes security, financial, or compliance incident. |
| Fallback returns null/empty/default without typed degraded state. | Users and operators cannot distinguish degradation from correctness. |
| Stale cache fallback has no max age. | Silent data-quality degradation persists indefinitely. |
| Circuit state has no metric or alert. | Operators cannot see that the system is degraded. |
| Shared thread/worker pool for all dependencies. | Optional slow dependency starves critical work. |
| Retry on 401/403/422. | Permanent failures create load, lockouts, and alert noise. |
| Feature flag default chosen for convenience. | Flag-service outage can enable unsafe behavior or disable core flow. |
| Fallback not tested. | Dead code path fails during the real outage. |

## Handoff Boundaries

- Use `idempotency-retry-design` when duplicate side effects or unknown timeout outcomes are primary.
- Use `cache-design` when stale/freshness/invalidation or cache stampede policy dominates.
- Use `failure-contract-design` when typed degraded, terminal, retryable, or user-safe failure semantics are primary.
- Use `configuration-runtime-policy` when flags, kill switches, provider modes, or config defaults control resilience.
- Use `observability` when metric names, logs, traces, dashboards, and alerts are the main output.
- Use `performance-budgeting` when latency, pool, fan-out, queue, or cost ceilings need measurable budgets.
- Use `security-privacy-gate` when fail-open, logs, fallback data, or dependency behavior affects auth, PII, secrets, or regulated flows.
- Use `delivery-release-gate` when canary, rollback, release watch, or production fault injection must be approved.
