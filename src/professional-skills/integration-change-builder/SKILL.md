---
name: integration-change-builder
description: "Use this skill when implementing, reviewing, planning, or validating product or code changes that need external integration changes across timeout, retry with backoff, circuit breaking, idempotency, webhook signature verification, replay protection, sandbox behavior, credentials, reconciliation, and operational failures."
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
metadata:
  changeforge.profile: recommended
  changeforge.skill_type: professional
---

# Integration Change Builder

## Mission
Design and review external integration changes so that every outbound call is bounded, authenticated, and idempotent; every inbound webhook is authenticated, replay-protected, and idempotent; every failure mode is detected, bounded, and recoverable; and every credential, rate limit, and reconciliation gap is explicitly managed — because integration bugs are silent, expensive, and often undetected until they cause financial or compliance damage.

## Stage Ownership
Own integration implementation placement for adapters, provider clients, webhooks, reconciliation jobs, sandbox behavior, credentials, idempotency, retries, timeouts, and circuit breakers. Use `logging-design-gate` for dependency latency, provider error translation, retry attempt, circuit state, timeout, fallback, and reconciliation diagnostics.

Do not own provider product selection, public API/schema shape, privacy approval, release rollout, SDK dependency policy, or business reconciliation thresholds when those decisions are primary; hand those slices to the named owner before closing integration implementation.

## When To Use
- Integrating with or modifying behavior for third-party REST APIs, SOAP services, or gRPC-based external services.
- Adding or modifying outbound webhooks to notify external systems of internal events.
- Receiving or modifying inbound webhooks from payment providers, identity providers, or SaaS platforms.
- Changing authentication mechanisms for external integrations (API key rotation, OAuth 2.0 client credentials, JWT assertions).
- Adding or modifying file-based exchange integrations (SFTP, S3-based partner feeds, EDI).
- Implementing rate limit handling, throttle backoff, or quota management for third-party APIs.
- Designing cross-system reconciliation or consistency verification for integration data.
- Migrating from one external provider to another (payment processor, email sender, SMS gateway).

## Do Not Use When
- The call is to an internal service within the same system boundary — use `backend-change-builder` for internal service-to-service calls.
- No external network, external credentials, or external ownership risk is involved.

## Adjacent Skill Conflict Resolution

For `integration-change-builder`, keep this skill primary only when external integration, timeout, retry, circuit breaker, idempotency, webhook signature, replay protection, sandbox, or provider contract behavior decides the next action. Hand API/schema compatibility to `data-api-contract-changer`, storage/query/migration concerns to `data-middleware-change-builder`, security/privacy decisions to `security-privacy-gate`, reliability/observability decisions to `reliability-observability-gate`, release/rollback readiness to `delivery-release-gate`, and documentation contract updates to `change-documentation-gate`. Domain extensions add risk-specific addenda after the primary owner is selected; record skipped plausible owners when the routing choice affects handoff or validation.

## Required Context / Missing Information Policy

Before `integration-change-builder` plans or closes work, collect current behavior, desired behavior, non-goals, affected surface, owner module, validation signal, existing conventions, and material data/API/security/release boundaries. Ask or block only when the missing fact can change public contract, data model, authorization, tenant behavior, migration/rollback, irreversible operation, or domain semantics; otherwise proceed with explicit reversible assumptions.

## Critical Gotchas

- `integration-change-builder` must inspect the owning source, tests, configs, docs, and generated-artifact boundaries before planning material engineering work.
- `integration-change-builder` must select only risk-changing references, capabilities, gates, or domain extensions; do not load nearby material because it exists.
- `integration-change-builder` must close with fresh validation evidence, evidence limits, residual risk, and next owner or gate when work remains.

## Non-Negotiable Rules
- **Direct use still runs the runtime prompt flow.** When `integration-change-builder` is invoked directly and router reclassification is skipped, target-project engineering work must still clarify requirements before action, inspect relevant code/tests/config/docs before planning, name a TDD or validation signal before implementation, map each action to an owner skill and a different review skill, repair and re-review findings, and hand off with validation evidence, residual risk, and route/stage manifests when routed.
- Non-trivial direct use still requires `repository-context-map` before planning when affected files, callers, local conventions, or source-of-truth boundaries are not already inspected.
- **Always set explicit timeouts on all outbound HTTP calls**: a missing timeout is an unbounded thread hold that cascades into request queue exhaustion; default `0` (no timeout) is never acceptable in production.
- **Retry with exponential backoff and jitter, with a bounded retry count**: unbounded retries amplify incidents and can trigger provider rate limits or account bans.
- **Idempotency is required for all commands that can be retried**: every outbound write, payment, or state-transition command must use idempotency keys to prevent duplication of effects on network retry.
- **All inbound webhook signatures must be verified before processing**: processing unauthenticated webhook payloads allows any actor to forge events and inject fraudulent state changes.
- **Replay protection is required for all inbound webhooks**: a nonce, timestamp check, or event ID deduplication store must prevent re-processing of replayed events.
- **Credentials must never be in source code, container images, or hardcoded configuration**: use secrets management (Vault, AWS Secrets Manager, GCP Secret Manager) with rotation support.
- **Sandbox testing is required before production integration**: every integration must be validated against the provider's sandbox environment with realistic test cases before any live credentials are used.
- **Reconciliation must be designed and scheduled**: any integration that transfers state, data, or money must have a reconciliation job that detects and alerts on drift between system state and provider state.
- **Circuit breakers are required for integrations on the critical path**: an unavailable external provider must not cascade into the unavailability of the consuming service.
- **Prefer provider and SDK primitives before custom integration machinery**: use official SDK clients, provider idempotency headers, webhook verification helpers, rate-limit headers, and existing retry/circuit policies before wrapper-only clients, custom retry loops, bespoke signature parsers, or generic provider abstractions.

## Industry Benchmarks
- **Release It! (Michael Nygard)**: Stability patterns — circuit breaker, timeout, bulkhead, fail fast. The canonical reference for integration resilience design.
- **OAuth 2.0 RFC 6749 / PKCE (RFC 7636) / Client Credentials**: Token lifecycle management, refresh token rotation, scope minimization. Standard for API authentication.
- **HMAC-SHA256 Webhook Signature Verification (Stripe, GitHub, Twilio)**: Provider-standard pattern for signing webhook payloads — compute HMAC over the raw payload body (not parsed body) with the shared secret; compare in constant time.
- **AWS Well-Architected Framework — Reliability Pillar**: Retry with exponential backoff and jitter; graceful degradation; bulkhead pattern for external call isolation.
- **PCI DSS (Payment Card Industry Data Security Standard)**: For payment integrations — never handle raw card data in application code; use hosted payment fields or tokenization APIs; audit all credential access.
- **NIST SP 800-63 (Digital Identity Guidelines)**: For identity provider integrations — token validation, claim verification, nonce-based replay protection for OIDC flows.
- **Google SRE Book — Chapter 21 (Handling Overload)**: Adaptive throttling, load shedding, and backpressure — applicable to all high-volume third-party API integrations.

### Integration Resilience Pattern Selection Matrix

| Integration Characteristic | Required Resilience Pattern | Configuration Notes |
|---|---|---|
| Synchronous on critical user path | Circuit breaker + timeout + bulkhead | Fail fast; return fallback or error; do not block user |
| Background batch processing | Retry with exponential backoff + DLQ | Max retries: 5; initial delay: 1s; max delay: 60s; jitter: ±25% |
| Payment or financial operation | Idempotency key + reconciliation job | Idempotency key: UUID v4; TTL: 24h; reconcile hourly |
| Inbound webhook from provider | HMAC signature verification + replay dedup | Verify before any processing; dedup window: 5 minutes |
| Long-running async operation | Polling with backoff OR webhook callback | Prefer webhook callback; poll only if provider does not support |
| High-volume data sync | Rate limit awareness + pagination + offset tracking | Respect `Retry-After` headers; checkpoint offset on failure |
| Provider migration (A → B) | Parallel run + shadow mode + reconcile | Run both, compare outputs; migrate traffic in stages |

## Technical Selection Criteria
Evaluate every integration change against:
- **Provider contract audit**: Is the provider's API versioned? What is the deprecation policy? Are rate limits and quota documented?
- **Timeout configuration**: Connection timeout (TCP handshake), read timeout (response body), and total request deadline — all three must be set.
- **Retry policy**: Max retry count, backoff algorithm (exponential + jitter), which HTTP status codes are retryable (429, 502, 503, 504 — not 400, 401, 403, 404).
- **Idempotency design**: Key source (UUID v4, client-generated), scope (per user, per operation), storage (database with TTL), and response on duplicate request.
- **Circuit breaker state machine**: Closed → Open (on failure threshold) → Half-Open (after cool-down) → Closed (on success). What is the failure threshold? Cool-down period?
- **Webhook authentication**: Is the signature algorithm provider-standard (HMAC-SHA256)? Is the raw body used for HMAC computation (not parsed body, which may be reformatted)?
- **Replay protection**: Is the event ID stored in a deduplication store? What is the dedup window? What happens when the dedup store is unavailable?
- **Credential lifecycle**: How are credentials stored? What is the rotation schedule? Who is notified when rotation is due? Is the rotation automated?
- **Sandbox parity**: Does the sandbox reproduce the provider's failure modes (rate limits, 5xx errors, timeout behavior) for testing?
- **Reconciliation frequency**: How frequently is reconciliation run? What drift threshold triggers an alert? Who is paged when drift exceeds threshold?
- **Minimal correctness**: Provider/SDK/native feature, existing integration boundary, or small adapter considered before new generic client, wrapper, retry/circuit component, config mode, or dependency.

## Trade-Offs
- **Verification before parsing**: raw-body signature and replay checks come before payload parsing, routing, logging, or mutation; convenience body parsers lose correctness evidence when the signed byte stream is changed.
- **Idempotency before retry**: outbound write retries come after idempotency key scope, duplicate response behavior, and provider support are verified; availability gains do not justify duplicate external side effects.
- **Provider primitive before wrapper**: official SDK clients, idempotency headers, webhook verifiers, rate-limit headers, and retry/circuit primitives come before custom provider abstractions unless sandbox evidence proves the primitive cannot satisfy the contract.
- **Reconciliation before optimistic success**: accepted, unknown, partial, and delayed provider states come before local finalization for money, entitlement, order, or identity changes; user-path speed does not replace drift detection.
- **Sandbox evidence before production rollout**: sandbox parity gaps, live-only rate limits, and untestable outage modes must be named before enabling production credentials, flags, or traffic splits.

## Mode Selection
Select the integration mode before changing outbound clients, webhooks, credentials, provider config, or reconciliation.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| New external integration | New provider, client, webhook, credential, data exchange, or file transfer. | Contract, timeouts, retries, idempotency, auth, sandbox, observability, reconciliation. | Provider docs/version, sandbox test plan, credential owner, failure modes. | `idempotency-retry-design`, `secret-configuration-security`, `reliability-observability-gate` | Custom abstraction until provider boundary is proven. |
| Modify existing integration | API version, endpoint, payload, rate limit, credential, or failure handling changes. | Preserve provider compatibility and old behavior during rollout. | Current config, call sites, provider changelog, sandbox/prod diff, regression tests. | `version-compatibility`, `quality-test-gate`, `delivery-release-gate` | Provider migration unless required. |
| Webhook ingest | Signature, replay, event routing, dedupe, DLQ, or event schema changes. | Verify before processing, dedupe/replay, idempotent side effects, observability. | Raw-body HMAC path, event ID store, retry/DLQ, duplicate-event test. | `web-security`, `message-queue-design`, `backend-change-builder` | Processing payload before verification. |
| Bug fix / incident | Timeout, 429, duplicate external charge/order, missed webhook, drift, credential expiry. | Verify cause, bound retry, reconcile drift, add regression/sandbox proof. | Logs/provider response, cause, same-pattern scan, reconciliation report. | `failure-diagnosis`, `agent-execution-discipline`, `reliability-observability-gate` | Retrying provider without idempotency evidence. |
| Provider migration/release | Provider A->B, version cutover, sandbox/prod config, credential rotation, traffic split. | Parallel run, rollback, reconciliation, rate-limit/cost guardrails. | Shadow comparison, rollback plan, config diff, staged rollout, owner. | `delivery-release-gate`, `change-documentation-gate`, `security-privacy-gate` | Big-bang provider switch. |
| Security/privacy-sensitive | IdP/payment/PII/PHI/financial data, OAuth, secrets, signed URLs, private files. | Data minimization, credential lifecycle, auth boundary, audit and compliance. | Secret store/rotation, DPA/compliance note, least privilege, audit event. | `security-privacy-gate`, `secret-configuration-security` | Plain env/log exposure of credentials. |

## Proactive Professional Triggers

- **Signal:** outbound HTTP call lacks connection/read/total timeout. **Hidden risk:** missing timeout causes silent request backlog, worker exhaustion, and cascading outage latency. **Required professional action:** require and verify explicit timeouts and failure behavior at the provider boundary. **Route to:** `reliability-observability-gate`, `backend-change-builder`. **Evidence required:** timeout config diff, timeout test output, and metric/log proof.
- **Signal:** provider client, SDK, token refresher, webhook verifier, or connection pool is constructed per call or through a hidden locator. **Hidden risk:** lifecycle leak, token churn, pool exhaustion, and untestable overrides. **Required professional action:** define dependency wiring and lifecycle. **Route to:** `dependency-wiring-lifecycle`, `implementation-structure-design`. **Evidence required:** composition root, lifecycle scope, construction/shutdown owner, and test override.
- **Signal:** retry policy lacks exponential backoff, jitter, max attempts, or `Retry-After` handling. **Hidden risk:** retry storm and provider ban. **Required professional action:** bound retry budget and aggregate rate. **Route to:** `idempotency-retry-design`, `performance-budgeting`. **Evidence required:** retry matrix, 429/5xx tests, rate-limit metric.
- **Signal:** retried external write has no idempotency key or duplicate response behavior. **Hidden risk:** duplicate payment/order/entitlement. **Required professional action:** require idempotent external call design. **Route to:** `idempotency-retry-design`, `payment-trading-extension` when money is involved. **Evidence required:** key scope, provider idempotency support, duplicate-request test.
- **Signal:** provider write can return timeout, 202/accepted, unknown, or partial success while local state moves forward. **Hidden risk:** external side effect succeeds after the caller records failure or retries. **Required professional action:** model accepted/unknown/failed states and reconciliation before release. **Route to:** `data-api-contract-changer`, `reliability-observability-gate`. **Evidence required:** state table, compensation/reconciliation path, timeout/unknown-result test.
- **Signal:** provider errors, SDK exceptions, webhook failures, or sandbox mismatches are collapsed into generic success/failure. **Hidden risk:** retryable, terminal, auth, throttling, timeout, and partial provider states become indistinguishable. **Required professional action:** define integration failure contract. **Route to:** `failure-contract-design`, `logging-error-handling`. **Evidence required:** provider-to-local translation map, retryability, safe diagnostics, and negative tests.
- **Signal:** provider version, SDK schema, webhook payload, or generated client changes without consumer review. **Hidden risk:** downstream consumer or provider contract break. **Required professional action:** run consumer impact analysis. **Route to:** `consumer-impact-analysis`, `version-compatibility`. **Evidence required:** changed contract, consumers, compatibility, migration/deprecation, telemetry, and rollback.
- **Signal:** provider SDK models, webhook payloads, generated clients, or adapter DTOs are passed directly into domain objects or API responses. **Hidden risk:** provider schema drift leaks into local contracts and domain behavior. **Required professional action:** map provider/local/API model boundaries. **Route to:** `model-boundary-mapping`, `data-api-contract-changer`. **Evidence required:** provider-to-local mapping owner, validation owner, null/default semantics, version compatibility, and mapping tests.
- **Signal:** integration tests require live providers, private adapter helpers, uncontrolled clocks/random IDs, or broad shared fixtures. **Hidden risk:** tests are flaky, expensive, or coupled to adapter internals instead of provider contract behavior. **Required professional action:** design test seams and pair doubles with contract or sandbox proof. **Route to:** `testability-seam-design`, `quality-test-gate`. **Evidence required:** provider seam map, fake/stub/contract/sandbox decision, deterministic controls, fixture owner, and test output.
- **Signal:** provider callback, webhook mapper, or adapter conversion mutates local state, cache, events, or external side effects before verification or durable commit. **Hidden risk:** forged, duplicate, or rolled-back provider events create inconsistent local state. **Required professional action:** trace integration side effects and ordering. **Route to:** `data-side-effect-flow-tracing`, `idempotency-retry-design`. **Evidence required:** flow map, verification point, transaction/outbox ordering, idempotency/compensation, and failure test.
- **Signal:** webhook handler parses or mutates before signature verification or lacks replay dedupe. **Hidden risk:** forged or replayed event. **Required professional action:** verify raw body before any processing and dedupe events. **Route to:** `web-security`, `security-privacy-gate`. **Evidence required:** raw-body HMAC test, constant-time compare, replay test.
- **Signal:** sandbox config differs from production for auth, endpoints, rate limits, failures, or schema. **Hidden risk:** sandbox tests do not predict production behavior and leave release risk unverified. **Required professional action:** document parity gaps and compensating validation before release. **Route to:** `delivery-release-gate`, `quality-test-gate`. **Evidence required:** sandbox/prod matrix, compensating validation output, untestable residual risk, and owner.
- **Signal:** state transfer integration has no reconciliation job or drift alert. **Hidden risk:** silent divergence after missed webhook or partial provider success. **Required professional action:** add reconciliation or accepted residual risk. **Route to:** `reliability-observability-gate`, `data-middleware-change-builder`. **Evidence required:** drift query, schedule, threshold, owner.
- **Signal:** credentials have no rotation owner, expiry monitoring, or audit trail. **Hidden risk:** expired or leaked integration secret. **Required professional action:** define lifecycle before release. **Route to:** `secret-configuration-security`, `security-privacy-gate`. **Evidence required:** secret store path, rotation plan, expiry alert.
- **Signal:** integration code adds a wrapper-only client, generic provider interface, custom retry/circuit breaker, signature verifier, polling framework, or extra dependency while provider SDK/runtime features already cover the need. **Hidden risk:** duplicate integration machinery drifts from provider semantics and hides failure behavior. **Required professional action:** run minimal-correctness review while preserving timeout, idempotency, webhook verification, and reconciliation obligations. **Route to:** `minimal-correct-implementation`, `package-dependency-management`, `reliability-observability-gate`. **Evidence required:** provider primitive considered, rejected wrapper/dependency path, sandbox test, and upgrade trigger if a shortcut remains.

### Decision Tree: Retry Policy

```
Did the request fail with 429 (Too Many Requests)?
├── Yes → Honor Retry-After header; if absent, use provider-specific backoff
Did the request fail with 5xx?
├── Yes → Retry with exponential backoff (1s → 2s → 4s → 8s → 16s) + jitter; max 5 retries
Did the request fail with 4xx (except 429)?
├── Yes → Do NOT retry — client error; log with full context; route to DLQ or alert
Did the request time out (connection or read timeout)?
├── Yes → Retry with backoff; verify idempotency key is sent on retry
Did the request succeed?
└── Record idempotency key response; return to caller
```

## Solution Optimality Self-Check
Apply when the change introduces or modifies outbound calls, retry logic, circuit breakers, webhooks, or provider dependencies. Answer the **Three-Challenge Rule** before finalizing: (1) why this approach over the alternatives, (2) is it the simplest sufficient design (a timed synchronous call before a queue + DLQ + reconciliation), (3) what is the strongest alternative and the specific cost that rejects it ("no reconciliation means undetected payment drift"). Then budget the performance dimensions — CPU, memory, network, disk, locks/contention, TPS/QPS, parallelism, concurrency, response latency — or mark each N/A with a one-line rationale.

Load [references/solution-optimality.md](references/solution-optimality.md) for the full integration performance-dimension matrix and additional considerations (retry-storm cost formula, Retry-After back-pressure, reconciliation) when the change touches a performance-sensitive path. Method compiled from `solution-optimality-evaluation`.

## Risk Escalation
- Escalate for all payment, financial, or money-movement integrations — PCI DSS scope, idempotency, and reconciliation are non-negotiable.
- Escalate when identity provider (IdP) integration changes affect authentication or authorization for any user — a misconfigured OIDC flow can lock out all users.
- Escalate when regulated data (PII, PHI, financial records) is exchanged with a third party — DPA, data processor agreement, and data minimization review required.
- Escalate when the integration is on the critical user path and the circuit breaker or timeout configuration is not validated.
- Escalate when the provider does not support sandbox testing — production integration without sandbox validation is a compliance and stability risk.
- Escalate when credential rotation has never been performed and the credentials are older than 90 days.
- Escalate when no reconciliation mechanism exists for an integration that transfers money, entitlements, or orders.
- Escalate when a webhook consumer processes events before signature verification — this is an active security vulnerability.

## Critical Details
- **HMAC signature verification must use the raw request body**: webhook libraries that parse the JSON body before signature verification can silently accept forged payloads when character encoding or whitespace differs from the expected string representation. Always compute HMAC over the raw byte stream from the request.
- **Constant-time comparison for HMAC verification**: use `hmac.compare_digest()` (Python) or equivalent — string equality `==` is susceptible to timing attacks that allow brute-force signature forgery.
- **Retry on timeout requires idempotency**: if a request timed out, the provider may have already processed it. Never retry a non-idempotent write without an idempotency key.
- **`Retry-After` header must be respected**: ignoring a provider's `Retry-After` header causes exponential retry storms that can result in account suspension or permanent bans.
- **Provider rate limits are per-account, not per-instance**: horizontal scaling of consuming services multiplies the rate of outbound requests — aggregate rate across all instances must stay within provider quota.
- **Webhook delivery is not guaranteed**: webhook providers typically retry on 5xx or timeout, but do not guarantee delivery. A reconciliation job is the safety net for missed events.
- **OAuth token rotation and refresh race**: when multiple instances refresh the same OAuth token simultaneously, the first refresh invalidates the second instance's cached token — use a distributed lock or token store.
- **File exchange integrity**: SFTP and S3-based file exchanges must include checksum verification (MD5 or SHA-256) to detect partial transfers or corruption.

## Anti-Patterns
- **Anti-pattern: parse-then-verify webhook.** Signal: handler reads JSON, logs fields, routes by event type, or mutates state before signature verification. Why wrong: the verified artifact is the raw byte stream, and parsed payloads can be forged, reformatted, or replayed. Required correction: verify HMAC/timestamp first, then dedupe and process.
- **Anti-pattern: retry as reliability proof.** Signal: timeout, 429, or 5xx handling adds more attempts without idempotency, `Retry-After`, max budget, or aggregate provider quota. Why wrong: retry can amplify outages and duplicate external writes. Required correction: idempotency before retry, exponential backoff with jitter, retryable-status matrix, and provider-account rate guard.
- **Anti-pattern: wrapper-only generic provider.** Signal: new generic client, adapter interface, retry helper, or SDK wrapper appears before provider primitives and existing integration boundaries are checked. Hidden risk: local abstractions drift from provider semantics and hide failure contracts. Replacement: use provider/native primitives or keep a narrow adapter with sandbox evidence and an upgrade trigger.

### Anti-Examples

| Integration Pattern | Problem | Corrected Approach |
|---|---|---|
| `requests.get(url)` — no timeout | Thread holds indefinitely on provider unavailability | `requests.get(url, timeout=(3.0, 30.0))` — connection timeout 3s, read timeout 30s |
| Retry all failures immediately, no limit | 500 error retried 1000x/minute — provider bans account | Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter; max 5 retries |
| Process webhook before signature check | Forged events inject fraudulent state | Verify `X-Stripe-Signature` HMAC first; reject 401 on failure; then process |
| API key in `config/secrets.yaml` in source repo | Credential leak via git history | Retrieve from Vault or AWS Secrets Manager at runtime; rotate on exposure |
| No reconciliation for payment webhooks | Missed `payment.succeeded` event = unconfirmed order forever | Hourly reconciliation job compares order status against provider payment status |

## Failure Modes
For `integration-change-builder`, state symptom, impact, and detection.
State repair and evidence before closure.

- **Unbounded retries amplify incidents**: a 5-second provider outage produces 50,000 retry requests per minute — the provider interprets it as a DDoS and bans the integration account.
- **Missing idempotency duplicates payment**: a payment request times out, the client retries without an idempotency key — the customer is charged twice; chargeback and reconciliation follow.
- **Unsigned webhook forged**: an attacker sends a crafted `payment.succeeded` event — order fulfillment is triggered without a real payment.
- **OAuth token invalidated mid-request**: a token refresh invalidates the token currently used by another in-flight request — all requests using the old token fail simultaneously.
- **Rate limit exceeded, no backoff**: an import job issues 10,000 requests in 60 seconds against a provider with a 100 requests/minute limit — all requests after the 100th fail with 429 and retry without delay, compounding the problem.
- **No reconciliation reveals drift**: a webhook delivery failure goes undetected — order state diverges from payment state for 72 hours until a user reports a discrepancy.
- **Credential expires during peak traffic**: an API key with no rotation monitoring expires — the integration silently fails for all users until an operator manually rotates the key.
- **Webhook body parsed before HMAC**: the web framework pretty-prints the JSON before HMAC computation — the signature never matches the provider's signature; all webhooks are rejected.

## Reference Loading Policy
Do not load every reference by default. For L1 `integration-change-builder` work, use this body unless selected risk requires more detail.
For L2, L3, L4, and L5 `integration-change-builder` work, read `references/capabilities/index.md` only to locate selected capability references; load selected files at `references/capabilities/<capability-id>-<capability-name>.md`, then add skill or domain references only when route risk requires them.
Load [references/checklist.md](references/checklist.md) when closing or reviewing an integration change and a compact gate checklist is needed without loading deeper capability references.

## Execution Procedure

For `integration-change-builder`: confirm activation and role; classify missing context; inspect relevant source/test/config/doc evidence; select mode, complexity, risk, and minimal references; execute or review only the owned surface; validate with concrete commands, diffs, tests, evals, or not-run limits; route repair through the owner; hand off with residual risk and next gate.

## Output Contract
Return an integration design with:
- **Mode selected**: new integration, modify existing, webhook ingest, bug/incident, provider migration, or security/privacy-sensitive, with trigger signal.
- **Boundaries inspected**: provider docs/version, client code, retry/circuit config, webhook verifier, credential store, sandbox/prod config, reconciliation job, rate limits, and release boundaries inspected or skipped with reason.
- **Professional judgment**: provider contract, timeout/retry/idempotency/webhook/security/reconciliation decision, and external failure risks ruled out or retained.
- **Provider contract**: API version, deprecation status, rate limits, quota, and sandbox availability.
- **Authentication design**: Credential type, storage location, rotation schedule, and rotation automation.
- **Dependency lifecycle**: provider client/SDK/pool/token refresher construction owner, lifecycle scope, startup validation, shutdown cleanup, and test override.
- **Resilience configuration**: Timeout values, retry policy, backoff algorithm, circuit breaker thresholds.
- **Failure contract**: provider/SDK/webhook error taxonomy, retryable versus terminal states, timeout/cancellation, partial success, safe user/internal messages, and cause preservation.
- **Idempotency design**: Key strategy, scope, storage, TTL, and duplicate-request handling.
- **Inbound webhook security**: Signature algorithm, verification implementation, replay protection mechanism.
- **Reconciliation plan**: Job schedule, drift threshold, alert owners, and remediation procedure.
- **Credential lifecycle plan**: Current storage, rotation schedule, expiry monitoring, and automated rotation if applicable.
- **Partial external success analysis**: provider accepted/unknown/failed states, timeout ambiguity, reconciliation and compensation.
- **Consumer impact**: changed provider/API/SDK/schema/event contract, known and unknown consumers, generated client impact, compatibility, migration, telemetry, and rollback.
- **Configuration runtime policy**: sandbox/prod config scope, typed config, safe defaults, validation, flag/kill switch owner, rollout/rollback, and cleanup path.
- **Reuse and placement rationale**: integration client, webhook verifier, credential store, retry/circuit config, and reconciliation job ownership and placement.
- **Minimal Correctness Decision**: provider/SDK/runtime primitive selected or rejected, wrapper/dependency avoided or justified, deleted/shrunk integration machinery, and shortcut ceiling with reconciliation or sandbox upgrade trigger.
- **Behavior preservation**: old provider behavior, event semantics, retry behavior, and rollback/migration compatibility preserved or intentionally changed.
- **Test obligations**: Sandbox tests (normal, timeout, rate-limit, signature-failure cases), idempotency tests, reconciliation tests.
- **Observability**: Metrics (success rate, latency, retry rate, circuit state, reconciliation drift), alert thresholds, and on-call routing.
- **Validation evidence**: sandbox/failure/security/reconciliation commands and validators run, exit code, report or artifact path, bounded output slice, what they prove/do not prove, residual risk, and next gate.
- **Evidence limits**: what each sandbox, webhook, retry, or reconciliation test proves and what it does not prove about production provider behavior, rate limits, or outage modes.

## Evidence Contract
Close an integration change only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the selected mode, provider contract, signature scheme, idempotency rule, or reconciliation requirement the change rests on, treating third-party failure as the expected case.
- **Files and boundaries inspected**: client, retry/circuit-breaker config, webhook verifier, credential store, sandbox/prod config, provider changelog, reconciliation job, and rate-limit boundary read.
- **Placement rationale**: why the timeout, retry budget, idempotency key, and reconciliation job live where they do, with dependency direction (via `implementation-structure-design`).
- **Validation commands**: sandbox tests for normal, timeout, rate-limit, partial success, and signature-failure cases plus idempotency and reconciliation tests, each with command or validator name, exit code, artifact/report path, outcome, what evidence proves, and what evidence does not prove.
- **Evidence quality classification**: strong evidence comes from current source plus sandbox/contract/security/reconciliation tests; weak evidence is config or code inspection without provider execution; missing evidence means a required boundary was not inspected; invalid evidence is stale, wrong-provider, wrong-environment, or lacks the raw webhook/request artifact.
- **Integration judgment and handoff**: mode selected, provider-failure judgment, behavior preservation, evidence limits, and next gate.
- **Residual risk**: retry-storm, replay, drift, provider outage, sandbox parity, rate limit, or credential-rotation path that remains untested or assumed, and the named owner of the follow-up.

## Quality Gate
1. All outbound HTTP calls have explicit connection timeout and read timeout configured.
2. Retry policy uses exponential backoff with jitter; max retry count is bounded; non-retryable 4xx errors are not retried.
3. All commands that can be retried use idempotency keys scoped to the operation.
4. All inbound webhook signatures are verified using HMAC over the raw request body before any processing.
5. Webhook replay protection is implemented with an event dedup store and a defined dedup window.
6. All credentials are stored in a secrets management service — not in source code, environment variables in logs, or container images.
7. Circuit breakers are configured for all integrations on the critical user path.
8. Sandbox validation has been performed with realistic test cases including failure modes.
9. A reconciliation mechanism exists for all integrations that transfer state, money, or entitlements.
10. Rate limit headers (`Retry-After`, `X-RateLimit-Remaining`) are handled correctly.

## Handoff
- **backend-change-builder** — for application-layer implementation of integration clients, circuit breakers, and webhook handlers.
- **security-privacy-gate** — for credential audit, data processor agreements, PCI DSS scope, and webhook security review.
- **reliability-observability-gate** — for circuit breaker metric alerts, integration SLO coverage, and on-call escalation paths.
- **quality-test-gate** — for sandbox test design, idempotency test obligations, and reconciliation test coverage.
- **data-api-contract-changer** — when integration changes affect API contracts shared with external consumers.
- **dependency-wiring-lifecycle** — when provider clients, SDKs, pools, token refreshers, or webhook verifiers need lifecycle ownership.
- **failure-contract-design** — when provider error translation, retryability, timeout, cancellation, or partial success semantics are unclear.
- **consumer-impact-analysis** — when provider, SDK, schema, webhook payload, or public integration contracts affect consumers.
- **configuration-runtime-policy** — when sandbox/prod config, feature flags, modes, or kill switches control integration behavior.
- **model-boundary-mapping** — when provider SDK models, generated clients, webhook payloads, adapter DTOs, or local domain/API models risk leakage.
- **testability-seam-design** — when integration tests need deterministic provider seams or risk private adapter coupling.
- **data-side-effect-flow-tracing** — when provider callbacks, webhooks, adapters, or reconciliation paths hide state-changing side effects.

## Completion Criteria
Integration changes are ready when all outbound calls have explicit timeouts, bounded retries with backoff, and idempotency keys; all inbound webhooks verify HMAC signatures over raw bodies and deduplicate events; all credentials are in secrets management with rotation schedules; circuit breakers are configured for critical-path integrations; sandbox validation covers normal and failure paths; a reconciliation job is scheduled with alerting; and the test suite covers timeout, rate-limit, signature-failure, and duplicate-event scenarios.
