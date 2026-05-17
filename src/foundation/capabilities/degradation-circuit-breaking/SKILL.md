---
name: degradation-circuit-breaking
description: Designs timeouts, fallbacks, bulkheads, graceful degradation, and circuit breakers so dependency failure does not collapse core flows where fallback is possible.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "68"
changeforge_version: 0.1.0
---

# Mission

Design **bounded, observable, product-safe degradation behavior** for every external dependency — specifying timeouts, retry policies, fallback values or behaviors, circuit breaker thresholds and recovery, bulkhead isolation, and explicit fail-open vs fail-closed decisions — so that the failure or slowdown of any optional, non-critical, or transient dependency cannot cascade into an outage of core user flows.

# When To Use

Use this capability when a change calls: external HTTP/gRPC APIs (payment gateways, identity providers, third-party services); internal microservices across a network boundary; message queues or event streams with availability SLAs; caches (Redis, Memcached) where miss has fallback behavior; search services (Elasticsearch, Solr) where a fallback response is acceptable; ML/AI model inference endpoints; feature flag services (LaunchDarkly, Split.io); notification services (email, SMS, push); analytics or logging sinks; CDN or asset delivery services; or any dependency whose unavailability could propagate to end users through latency accumulation or error propagation.

# Do Not Use When

Do not use this capability to hide genuine correctness requirements. If a dependency is **required for correct behavior** (payment authorization, identity verification, data integrity check), the system must **fail closed** — no silent degradation. This capability designs degradation; it does not approve degradation of critical flows. Do not use it to avoid fixing an unreliable dependency; the root cause should also be addressed. Do not use it to silently drop irreversible operations (financial writes, audit records) without explicit product owner approval for that behavior.

# Non-Negotiable Rules

- **Every external dependency call has a timeout.** No call may block indefinitely. Timeout values are explicit and documented: `connection_timeout` (time to establish connection) and `read_timeout` (time to receive full response) are configured separately. Default "no timeout" is always wrong in production.
- **Retries are bounded and apply only to idempotent or safe operations.** Retry policy specifies: max attempts, backoff algorithm (exponential + jitter), max backoff delay, retryable error conditions (5xx, network timeout, `ETIMEDOUT`), and non-retryable conditions (4xx, auth errors, idempotency violations). Never retry a non-idempotent write without an idempotency key and duplicate-detection mechanism.
- **Fallback behavior is a product decision, not an engineering default.** "Return null" may mean "show the user nothing." "Return stale cache" may mean "show the user data from 4 hours ago." "Proceed without fraud check" may mean "approve a fraudulent transaction." Each fallback must be explicitly approved by the product owner with awareness of its user and business impact.
- **Circuit breaker thresholds are defined, not left at library defaults.** At minimum: failure rate threshold (e.g., `50% over 20 calls`), minimum request volume before tripping (`≥ 10 requests`), open state duration before half-open probe, probe success threshold to close. Library defaults (Hystrix, Resilience4j, Polly) may not match the traffic patterns of the service.
- **Fail-open vs fail-closed is a security and correctness decision.** Fail-open (allow action if dependency unavailable) is appropriate for: non-critical features, analytics, soft personalization. Fail-closed (deny action if dependency unavailable) is required for: authentication, authorization, fraud detection, compliance checks, payment authorization. An availability blip must not accidentally grant elevated access.
- **Bulkheads prevent a failing dependency from exhausting shared resources.** A downstream dependency that is slow causes threads (or goroutines, tasks) to accumulate if the thread pool is shared. Use thread pool isolation or semaphore isolation per dependency to cap the impact. Without bulkheading, one slow dependency can exhaust the entire server's request-handling capacity.
- **Degraded state is observable.** Circuit breaker state changes (CLOSED → OPEN → HALF-OPEN → CLOSED), fallback invocations, and timeout events are emitted as metrics and structured log events. SRE/ops can see: which circuit is open, when it opened, how many requests are being absorbed by fallback, and what the recovery rate is.
- **Stale fallback data has an explicit maximum staleness tolerance.** If a cache miss falls back to a stale value, the maximum acceptable age is defined and enforced. "Return whatever is in cache" without a staleness limit is not a fallback; it is silent data quality degradation.
- **Chaos and resilience tests verify degradation behavior.** Fallback paths that are never triggered in production are not tested by normal test suites. Circuit breaker behavior requires fault injection: `chaos-monkey`, `tc netem` (network emulation), `toxiproxy`, or platform-level fault injection (AWS Fault Injection Simulator, Gremlin).

# Industry Benchmarks

Anchor against: **Michael Nygard "Release It!" (2nd ed., 2018)** — canonical reference for timeout, circuit breaker, bulkhead, and fail-fast patterns; coined "circuit breaker" for software. **Netflix Hystrix** (now in maintenance; concepts still canonical) — thread pool isolation, circuit breaker, fallback chain; original production-scale circuit breaker. **Resilience4j** (Java) — Hystrix successor; circuit breaker, rate limiter, retry, bulkhead; Micrometer metrics. **Polly** (.NET) — circuit breaker, retry, timeout, bulkhead. **Envoy / Istio service mesh** — circuit breaking and outlier detection at the infrastructure layer (no code required); `outlierDetection` and `connectionPool` configuration. **AWS SDK retry configuration** — exponential backoff with jitter (https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/). **Google SRE Book** Ch. 19 (Front-end Infrastructure / Load Balancing) and Ch. 21 (Handling Overload) — request hedging, load shedding, backpressure. **CNCF Chaos Engineering principles** (Chaos Monkey, LitmusChaos, Gremlin) — verify resilience by injecting faults. **RFC 7807 / RFC 9457** — Problem Details used in degraded response bodies to communicate the fallback state to clients. **OWASP API Top 10 (2023)** — API4:2023 Unrestricted Resource Consumption relates to timeout and rate-limit discipline. **Martin Fowler "Patterns of Enterprise Application Architecture"** — Gateway pattern for wrapping third-party dependencies. **Toxiproxy** (Shopify) — TCP proxy for simulating network conditions (latency, bandwidth, timeouts) in tests. **AWS Fault Injection Simulator (FIS)** — production-grade chaos engineering. **Alibaba Sentinel** — flow control, circuit breaking, system adaptive protection for microservices.

### Dependency Criticality Classification

| Criticality | Definition | Failure policy | Example |
| --- | --- | --- | --- |
| **CRITICAL-CLOSED** | Required for correctness or security | Fail closed; return error; no silent degradation | Auth service, payment authorization, fraud check |
| **CRITICAL-DEGRADABLE** | Required for core flow but has safe fallback | Retry then defined fallback; alert immediately | Primary DB (→ read replica fallback); price service (→ cached price with age shown) |
| **OPTIONAL-DEGRADABLE** | Enhances experience; safe to omit | Return empty/null; log; no user-visible error | Recommendations, personalization, analytics |
| **FIRE-AND-FORGET** | Side effect; no user impact if lost | Queue + retry; drop if queue full with metric | Audit log sink, event tracking, notification |
| **SOFT-REALTIME** | Affects UX if slow, not if absent | Timeout aggressively (< 200ms); return empty | Feature flags, A/B test assignment |

### Timeout Configuration Decision Tree

```
Is this call on the critical path (synchronous, user-facing)?
├─ Yes →
│   Is this a connection establishment?
│   ├─ Yes → connection_timeout: 1–3s (network latency + TLS)
│   └─ No  → read_timeout: P99 latency × 2, max 5s for user-facing calls
│             (e.g., P99 = 800ms → read_timeout = 1600ms, capped at 5s)
└─ No (background, async, batch) →
    read_timeout: P99 × 3, up to 30s; circuit break at sustained high latency

Is the dependency in the same datacenter / VPC?
├─ Yes → connection_timeout: 500ms; read_timeout: P99 × 2
└─ No  (cross-region, public internet) → connection_timeout: 3s; read_timeout: 10s max for non-user-facing

Is there a cascading timeout budget (upstream caller has a shorter timeout)?
└─ Yes → downstream timeout < upstream timeout - 20% buffer
         (e.g., upstream read_timeout = 3s → downstream read_timeout ≤ 2400ms)
```

### Circuit Breaker Configuration Matrix

| Parameter | Conservative | Standard | Aggressive | Notes |
| --- | --- | --- | --- | --- |
| **Failure rate threshold** | 20% | 50% | 80% | % of requests that must fail before opening |
| **Minimum request volume** | 5 | 10 | 20 | Avoids tripping on cold traffic |
| **Sliding window size** | 10 calls | 20 calls | 50 calls | Count-based or time-based (e.g., 60s) |
| **Open state duration** | 5s | 10s | 30s | Time before half-open probe attempt |
| **Half-open probe count** | 1 | 3 | 5 | Requests allowed in half-open before deciding |
| **Probe success threshold** | 1 success | 2 successes | 3 successes | Required to close circuit |
| **Pick when** | Payment, auth | General services | High-volume logging/analytics | Match to criticality |

### Retry Policy Design

```
Retryable error conditions (RETRY):
  - HTTP 500, 502, 503, 504
  - Connection timeout (ETIMEDOUT, ECONNRESET)
  - gRPC UNAVAILABLE, RESOURCE_EXHAUSTED

Non-retryable conditions (FAIL IMMEDIATELY):
  - HTTP 400, 401, 403, 404, 409, 422 (client errors; retrying doesn't help)
  - gRPC INVALID_ARGUMENT, NOT_FOUND, PERMISSION_DENIED
  - Idempotency key collision (HTTP 409 with specific error code)

Retry backoff:
  sleep = min(cap, base * 2^attempt) + random(0, jitter)
  e.g.: base=100ms, cap=10s, jitter=±50ms
  Attempt 1: ~100ms; Attempt 2: ~200ms; Attempt 3: ~400ms; Attempt 4: ~800ms

Max attempts:
  User-facing synchronous: 2–3 attempts (stay within timeout budget)
  Background async: 5–10 attempts; exponential up to 30s
  Dead letter queue: after max attempts, route to DLQ with full context
```

### Bulkhead Sizing

```
Thread pool bulkhead (per downstream dependency):
  pool_size = (dependency_P99_latency_ms / 1000) × dependency_RPS × 1.3 (20% buffer)
  queue_size = pool_size × 2 (bounded; reject when full → 503 fast-fail)
  
  Example: dependency P99 = 200ms, expected RPS = 100
  pool_size = (200/1000) × 100 × 1.3 = 26 threads
  queue_size = 52

Semaphore bulkhead (for async/non-blocking calls):
  max_concurrent = dependency_RPS × dependency_P99_latency_s × 1.5
```

### Anti-examples

| Anti-pattern | Failure mode |
| --- | --- |
| No timeout on HTTP client | One slow dependency queues all threads; server unresponsive; cascading outage |
| `retry: 3` on `POST /payments` without idempotency key | Payment charged 3 times on transient 500 response |
| Circuit breaker at library default (50% threshold, 5 calls) | Trips on 3 failures during warm-up; healthy service appears broken; false positive outage |
| Auth service: fail-open ("if unavailable, allow") | Availability blip grants access to all resources to all users |
| "Return null" fallback for pricing service without product approval | Items shown with $0 price; financial loss |
| No circuit breaker state metric | Circuit opens; nobody knows; fallback runs for 72 hours silently |
| Retry on HTTP 401 | 10 retries × auth failure = 10 failed auth attempts; account lockout triggered |
| Shared thread pool for all downstream services | Analytics sink becomes slow; exhausts threads; payment service requests queue; outage |
| Stale cache fallback with no age limit | Cache shows data 2 weeks old; no observable signal; silent data quality issue |
| Fallback not tested | 2 years later, fallback code has a bug; discovered only during actual outage |

# Selection Rules

Select this capability when **dependency failure or cascading outage risk** is primary. Adjacent routing:

- Prefer `idempotency-retry-design` when the retry safety of a non-idempotent operation is the primary concern.
- Prefer `cache-design` when stale fallback behavior and cache invalidation policy are the primary design decisions.
- Prefer `observability` when the primary work is designing metrics, dashboards, and alerting for dependency health.
- Prefer `integration-change-builder` when the primary concern is the integration protocol or contract with a third-party service.
- Prefer `reliability-observability-gate` for overall system resilience assessment at release time.

# Risk Escalation Rules

Escalate when: a fail-open decision affects authentication, authorization, fraud detection, compliance validation, or payment authorization; fallback behavior silently drops irreversible writes (financial, audit, legal); stale fallback data has financial, regulatory, or contractual implications; a circuit breaker configuration change is being made to a dependency that handles PII, payments, or secrets; the degraded behavior is complex enough that testing requires production traffic (shadow mode required); the dependency failure mode could affect all tenants simultaneously (shared-infrastructure blast radius); chaos engineering requires injecting faults into a production environment.

# Critical Details

Resilience patterns are only as good as their configuration and observability. Precision failures:

- **Cascading timeouts.** If service A calls service B with a 10s timeout, and B calls C with a 10s timeout, A's request may accumulate up to 20s of latency before failing. Timeout budgets must flow downstream: each level's timeout must be shorter than the upstream caller's. Set `timeout = upstream_timeout × 0.7` as a maximum for each hop.
- **Retry amplification.** 3 clients each retrying 3 times on a struggling service = 9× load. Under high fan-out, retry storms accelerate the dependency's failure. Add circuit breakers **before** retries in the call stack to cut off retries when the circuit is open.
- **Jitter is not optional.** Without jitter, all callers that hit a timeout simultaneously will retry simultaneously — synchronized retry wave. `full jitter` (`random(0, base * 2^attempt)`) or `equal jitter` fully randomizes retry timing and prevents waves.
- **Fallback must be tested independently.** The fallback code path is never exercised in normal operation. Write a specific test (unit test with stubbed failure + chaos test with real fault injection) that exercises the fallback path. An untested fallback is a bug waiting for an outage.
- **Service mesh vs in-process circuit breakers.** Envoy/Istio implements circuit breaking at the infrastructure layer (no code changes required); it is more consistent but less business-logic-aware. In-process (Resilience4j, Polly) is more flexible and aware of business context (e.g., circuit-break only on specific operations). Use mesh-level for network-layer resilience + in-process for business-logic-aware fallbacks.
- **Feature flag service availability.** Feature flag services are themselves dependencies. If a flag evaluation times out and the default is "feature off," a flag service outage disables all gated features. If the default is "feature on," an outage enables all features. Both are risky. Evaluate: flag defaults must match the safe production state.
- **Half-open probe with high traffic.** In half-open state, the circuit allows a probe request. If the service is still struggling, this probe triggers another failure and reopens. With high traffic, the probe may also trigger significant load on a recovering service. Use a minimal probe (health check endpoint) rather than a full production request.

# Failure Modes

- No timeout configured on HTTP client; one dependency starts taking 30s per request; thread pool fills; server stops responding.
- Retry on non-idempotent POST; transient 503 causes 3 payment charges; customer and bank both charged.
- Circuit breaker trips on startup cold traffic (3 calls, 2 fail = 66%); healthy service classified as broken for 30s.
- Auth service configured as fail-open; 15-minute availability incident grants unauthenticated access to all users.
- Fallback code has bug introduced 8 months ago; never executed; discovered during first actual outage; additional 45 minutes of impact.
- Retry without jitter; 500 clients all retry after exactly 1s; second wave hits recovering service; re-triggers failure.
- Downstream timeout = 10s; upstream timeout = 8s; downstream never reaches its timeout; upstream always times out first; downstream connection leaks.
- Circuit breaker state not exported to metrics; ops unaware circuit is open for 6 hours; all requests absorbing fallback silently.
- Bulkhead not configured; slow analytics dependency fills shared thread pool; payment processing requests queue behind analytics calls; checkout fails.
- Stale cache fallback with no max-age; pricing data is 3 weeks old; promotion prices shown after promotion ended; revenue loss.
- `retry: 10` on HTTP 401; auth service returns 401 for malformed token; 10 auth attempts per request; triggers account lockout for 1000 users.
- Feature flag service unavailable; default is "feature off"; all new checkout flow gated features disabled; 40% revenue drop for 20 minutes.

# Output Contract

Return a resilience plan with:

- `dependencies` (per dependency: name, criticality class, protocol, P50/P99 latency, availability SLA)
- `timeout_config` (per dependency: connection_timeout, read_timeout, total_budget, justification)
- `retry_policy` (per dependency: max_attempts, backoff_algorithm, jitter, retryable_errors, non_retryable_errors, idempotency_requirement)
- `circuit_breaker` (per dependency: library/layer, failure_rate_threshold, min_requests, window_size, open_duration, half_open_probes, close_threshold)
- `bulkhead` (per dependency: isolation_type — thread pool/semaphore, pool_size, queue_size, reject_behavior)
- `fallback_behavior` (per dependency: fallback type, fallback value, staleness_limit, product_owner_approval, user_impact_description)
- `fail_open_vs_closed` (per dependency: decision, security/correctness justification)
- `stale_tolerance` (per cache fallback: maximum acceptable age, enforcement mechanism)
- `observability` (metrics emitted: circuit_state, fallback_count, timeout_count, retry_count; dashboard; alert thresholds)
- `chaos_tests` (test scenarios: fault type, injection tool, expected behavior, pass criterion)
- `cascade_analysis` (timeout budget chain from client → API → dependencies; amplification risk)

# Quality Gate

The resilience plan passes only when:

1. Every external dependency call has an explicit connection timeout and read timeout.
2. Retry policies specify: max attempts, backoff + jitter, retryable error conditions, and non-retryable conditions.
3. Non-idempotent operations are not retried without idempotency key + deduplication.
4. Fail-open vs fail-closed is explicitly decided per dependency with security/correctness justification.
5. Circuit breaker thresholds are customized for the service's traffic volume and criticality (not library defaults).
6. Bulkhead is configured for dependencies at risk of exhausting shared resources.
7. Fallback behavior has explicit product owner approval and user impact description.
8. Stale cache fallbacks have a defined maximum staleness.
9. Circuit breaker state changes, fallback invocations, and timeout events are emitted as metrics.
10. Fallback paths are covered by a specific test (unit test with stubbed failure or chaos test).

# Used By

- reliability-observability-gate
- integration-change-builder

# Handoff

Hand off to `idempotency-retry-design` for retry safety of non-idempotent operations; `cache-design` for stale fallback policy; `observability` for metric design and alerting; `integration-change-builder` for third-party protocol behavior; `reliability-observability-gate` for overall system resilience assessment.

# Completion Criteria

The capability is complete when **every external dependency has a defined and tested failure behavior** — timeout, retry policy, circuit breaker configuration, bulkhead isolation, fallback behavior with explicit product approval, and observable state — so that no single dependency outage can cascade into an uncontrolled core-flow failure.
