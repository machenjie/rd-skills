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

# Stage Fit

Own resilience design during planning, implementation review, testing, release preparation, and incident repair when dependency failure, timeout, overload, or fallback can affect a core flow. In planning, turn current source, dependency graph, project memory, execution trajectory, SLOs, retry budgets, and product criticality into fail-open/closed, timeout, fallback, circuit, bulkhead, and observability decisions. In review, reject stale "safe fallback", "optional dependency", "library default is fine", or "circuit already protects it" claims unless current source, telemetry, and validation confirm them. Hand off when the unresolved question is retry/idempotency, cache freshness, public failure contract, config/kill-switch lifecycle, observability, release readiness, or security/privacy.

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

# Mode Matrix

Select the degradation mode before choosing timeout, fallback, circuit, bulkhead, load-shed, or recovery mechanics.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Critical fail-closed dependency | Auth, authorization, fraud, payment, compliance, tenant isolation, or data integrity dependency. | Preserve correctness and security while bounding latency. | Criticality class, denied/degraded outcome, timeout, user-safe error, alert. | `failure-contract-design`, `security-privacy-gate` | Silent fallback or fail-open. |
| Optional graceful degradation | Recommendations, personalization, analytics, search refinement, notification, model inference, or non-core enhancement. | Keep core flow available with explicit degraded state. | Product approval, fallback contract, user impact, metric/log/trace signal. | `observability`, `frontend-change-builder` when UX changes | Null/empty default without typed state. |
| Latency budget protection | External call, cache miss, model call, queue, or service hop risks exceeding upstream deadline. | Timeout budget chain and bounded wait. | Upstream/downstream deadline, P95/P99 baseline or not-verified limit, abort behavior. | `performance-budgeting`, `language-performance-safety` | Timeout from library defaults. |
| Retry storm and circuit control | Retry, backoff, throttling, 429/503, SDK retry, or provider saturation. | Prevent amplification and cut load before cascade. | Retry budget, idempotency proof, circuit thresholds, open/half-open behavior. | `idempotency-retry-design`, `concurrency-control` | Retrying non-idempotent writes. |
| Bulkhead and load shedding | Shared pool, fan-out, worker pool, queue, cache stampede, or hot dependency. | Isolate resource exhaustion and fail fast under pressure. | Pool/queue/concurrency bound, reject behavior, backpressure metric, SLO impact. | `performance-budgeting`, `observability` | Global locks or unbounded queues. |
| Resilience repair or drill | Incident, chaos test, failing fallback, open circuit, timeout cascade, or stale degraded mode. | Verify cause, repair controls, and prove recovery. | Baseline, fault injection, before/after signal, rollback/disable path. | `failure-diagnosis`, `quality-test-gate` | Third same-path retry without route repair. |

# Industry Benchmarks

Anchor against Nygard's **Release It!**, Google SRE overload and error-budget practice, Hystrix/Resilience4j/Polly circuit-breaker patterns, Envoy/Istio outlier detection, AWS exponential backoff with jitter, Toxiproxy/Fault Injection Simulator resilience testing, RFC 7807/RFC 9457 degraded problem details, and OWASP API resource-consumption controls. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for dependency criticality matrices, timeout/circuit/retry/bulkhead patterns, graph/memory/trajectory coupling, resilience evidence examples, and anti-pattern review.

# Selection Rules

Select this capability when **dependency failure or cascading outage risk** is primary. Adjacent routing:

- Prefer `idempotency-retry-design` when the retry safety of a non-idempotent operation is the primary concern.
- Prefer `cache-design` when stale fallback behavior and cache invalidation policy are the primary design decisions.
- Prefer `observability` when the primary work is designing metrics, dashboards, and alerting for dependency health.
- Prefer `integration-change-builder` when the primary concern is the integration protocol or contract with a third-party service.
- Prefer `reliability-observability-gate` for overall system resilience assessment at release time.

# Risk Escalation Rules

Escalate when: a fail-open decision affects authentication, authorization, fraud detection, compliance validation, or payment authorization; fallback behavior silently drops irreversible writes (financial, audit, legal); stale fallback data has financial, regulatory, or contractual implications; a circuit breaker configuration change is being made to a dependency that handles PII, payments, or secrets; the degraded behavior is complex enough that testing requires production traffic (shadow mode required); the dependency failure mode could affect all tenants simultaneously (shared-infrastructure blast radius); chaos engineering requires injecting faults into a production environment.

# Proactive Professional Triggers

- **Signal:** project memory, repository graph, or prior execution says a dependency is optional, already protected, or safe to degrade without current confirmation. **Hidden risk:** stale context approves a fallback that no longer matches current callers, SLOs, tenants, or product criticality. **Required professional action:** confirm current source, call graph, dependency ownership, telemetry, and validation freshness. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, freshness limits, and unknown dependency disclosure.
- **Signal:** external HTTP/gRPC/SDK/cache/search/model/feature-flag call lacks explicit deadline, timeout, cancellation, or owner. **Hidden risk:** one slow dependency can consume request budget and pool capacity until the core flow fails. **Required professional action:** define timeout budget chain and cancellation behavior before handoff. **Route to:** `performance-budgeting`, `failure-contract-design`. **Evidence required:** upstream deadline, dependency P99 or not-verified limit, timeout values, and user-safe timeout result.
- **Signal:** fallback returns null, empty/default data, stale cache, or "skip" without a typed degraded state. **Hidden risk:** degraded mode is indistinguishable from correctness, data loss, or product absence. **Required professional action:** define fallback contract, product approval, user impact, and observability. **Route to:** `failure-contract-design`, `observability`. **Evidence required:** degraded response, product owner approval, metric/log/trace field, and test.
- **Signal:** retries are configured without idempotency proof, retry budget, jitter, or circuit interaction. **Hidden risk:** retry amplification worsens the outage and can duplicate side effects. **Required professional action:** bound retries and prove safe duplicate behavior. **Route to:** `idempotency-retry-design`, `concurrency-control`. **Evidence required:** retryable/non-retryable list, backoff/jitter, max attempts, idempotency key, and retry-load estimate.
- **Signal:** circuit breaker uses library defaults or lacks half-open probes, reset behavior, or state metrics. **Hidden risk:** false trips, stuck-open circuits, or silent degraded operation. **Required professional action:** calibrate circuit thresholds to traffic and criticality. **Route to:** `reliability-observability-gate`, `observability`. **Evidence required:** window, min volume, open duration, probe count, close threshold, dashboard signal.
- **Signal:** dependency failure can exhaust shared pool, worker, queue, thread, coroutine, DB connection, or fan-out capacity. **Hidden risk:** optional dependency failure takes down unrelated critical flows. **Required professional action:** add bulkhead, load shedding, backpressure, or bounded concurrency. **Route to:** `performance-budgeting`, `language-performance-safety`, `concurrency-control`. **Evidence required:** pool/queue/fan-out ceiling, reject behavior, saturation metric, and load/fault test or not-verified limit.
- **Signal:** feature flag, kill switch, provider mode, or runtime config controls degradation behavior without owner, typed default, rollback, or cleanup. **Hidden risk:** production mitigation depends on ungoverned config and can invert safe defaults. **Required professional action:** apply runtime config policy. **Route to:** `configuration-runtime-policy`, `delivery-release-gate`. **Evidence required:** config schema, safe default, owner, rollout/rollback, telemetry, and cleanup path.

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

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 degradation selection, safety, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete resilience plan, before implementation starts, or when timeout, fallback, circuit, bulkhead, observability, product approval, or recovery evidence is uncertain. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when dependency criticality, timeout/circuit/retry/bulkhead matrices, chaos testing, graph/memory/trajectory reuse, resilience evidence, or anti-pattern detail needs depth. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Output Contract

Return a resilience plan with:

- `mode_selected` (critical fail-closed, optional graceful degradation, latency budget protection, retry storm/circuit control, bulkhead/load shedding, or resilience repair/drill)
- `resilience_evidence` (current source paths, dependency graph, project memory, execution trajectory, SLOs, telemetry, runbooks, tests, and validation freshness inspected)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for every graph/memory/trajectory claim that affects safety)
- `dependencies` (per dependency: name, criticality class, protocol, P50/P99 latency, availability SLA)
- `protected_flows` (core user, admin, worker, batch, or operational flows protected from cascade)
- `timeout_config` (per dependency: connection_timeout, read_timeout, total_budget, justification)
- `retry_policy` (per dependency: max_attempts, backoff_algorithm, jitter, retryable_errors, non_retryable_errors, idempotency_requirement)
- `circuit_breaker` (per dependency: library/layer, failure_rate_threshold, min_requests, window_size, open_duration, half_open_probes, close_threshold)
- `bulkhead_load_shedding` (per dependency: isolation_type, pool_size, queue_size, max_concurrent, shed/reject behavior)
- `fallback_behavior` (per dependency: fallback type, fallback value, staleness_limit, product_owner_approval, user_impact_description)
- `degradation_contract` (typed degraded response/state, safe user message, retryability, terminal behavior, and recovery signal)
- `fail_open_vs_closed` (per dependency: decision, security/correctness justification)
- `stale_tolerance` (per cache fallback: maximum acceptable age, enforcement mechanism)
- `config_and_kill_switches` (safe defaults, owner, typed validation, rollout/rollback, cleanup path)
- `observability` (metrics emitted: circuit_state, fallback_count, timeout_count, retry_count; dashboard; alert thresholds)
- `chaos_tests` (test scenarios: fault type, injection tool, expected behavior, pass criterion)
- `cascade_analysis` (timeout budget chain from client → API → dependencies; amplification risk)
- `changed_degradation_to_validation_map` (each timeout, retry, circuit, bulkhead, fallback, degraded response, config, metric, and test mapped to validator or residual risk)
- `handoff_boundaries` (what belongs to retry/idempotency, cache freshness, failure contract, config, observability, release, security, or no-next-gate rationale)
- `evidence_limits` (what was not verified, such as production traffic shape, provider behavior, all tenants, chaos environment, SLO baseline, or recovery drill)

# Evidence Contract

Close a resilience plan only when the output names selected mode, current resilience evidence inspected, graph/memory/execution reuse judgment, protected flow and dependency criticality, fail-open/closed decision, timeout budget chain, retry/circuit/bulkhead/fallback configuration, typed degraded response, observability signals, chaos or targeted test evidence, changed-degradation-to-validation map, handoff boundaries, residual risk, and evidence limits. A statement like "add circuit breaker and fallback" is not sufficient evidence.

# Benchmark Coverage

Improved degradation plans should reject no-timeout clients, retries on non-idempotent writes, library-default breakers, fail-open auth/payment/fraud/compliance checks, null or empty fallback without typed degraded state, no circuit-state metric, shared pools without bulkhead, stale cache fallback without max age, unsafe feature-flag defaults, and untested fallback paths. Detailed matrices and examples belong in references so this body stays efficient.

# Routing Coverage

Route here when the primary work is dependency failure containment: timeout, fallback, circuit breaker, bulkhead, load shedding, fail-open/closed policy, stale fallback, or graceful degradation. Hand off when the primary concern is duplicate-effect retry lifecycle (`idempotency-retry-design`), cache freshness/invalidation (`cache-design`), typed boundary errors (`failure-contract-design`), runtime config or kill-switch lifecycle (`configuration-runtime-policy`), telemetry design (`observability`), release/watch/rollback (`delivery-release-gate`), or security/privacy of a fail-open decision (`security-privacy-gate`).

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
11. Repository graph, project memory, and execution trajectory inputs are current-source confirmed or marked not verified before they shape fail-open/closed, fallback, circuit, or recovery decisions.
12. Every timeout, retry, circuit, bulkhead, fallback, degraded response, config, metric, and chaos/test decision maps to validation evidence or named residual risk.
13. Degraded responses are typed and distinguishable from normal correctness, validation failure, permission denial, and terminal dependency failure.
14. Config, feature flag, provider-mode, and kill-switch degradation controls have typed validation, safe default, owner, rollout/rollback path, observability, and cleanup path.
15. Handoff boundaries and evidence limits are explicit so degradation design is not over-claimed as retry safety, cache correctness, public API failure contract, production release readiness, or security approval.

# Used By

- reliability-observability-gate
- integration-change-builder

# Handoff

Hand off to `idempotency-retry-design` for retry safety of non-idempotent operations; `cache-design` for stale fallback policy; `observability` for metric design and alerting; `integration-change-builder` for third-party protocol behavior; `reliability-observability-gate` for overall system resilience assessment.

# Completion Criteria

The capability is complete when **every external dependency has a defined and tested failure behavior** — timeout, retry policy, circuit breaker configuration, bulkhead isolation, fallback behavior with explicit product approval, and observable state — so that no single dependency outage can cascade into an uncontrolled core-flow failure.
