---
name: integration-change-builder
description: Guides external integration changes across timeout, retry with backoff, circuit breaking, idempotency, webhook signature verification, replay protection, sandbox behavior, credentials, reconciliation, and operational failure handling.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Integration Change Builder

## Mission
Design and review external integration changes so that every outbound call is bounded, authenticated, and idempotent; every inbound webhook is authenticated, replay-protected, and idempotent; every failure mode is detected, bounded, and recoverable; and every credential, rate limit, and reconciliation gap is explicitly managed — because integration bugs are silent, expensive, and often undetected until they cause financial or compliance damage.

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

## Non-Negotiable Rules
- **Always set explicit timeouts on all outbound HTTP calls**: a missing timeout is an unbounded thread hold that cascades into request queue exhaustion; default `0` (no timeout) is never acceptable in production.
- **Retry with exponential backoff and jitter, with a bounded retry count**: unbounded retries amplify incidents and can trigger provider rate limits or account bans.
- **Idempotency is required for all commands that can be retried**: every outbound write, payment, or state-transition command must use idempotency keys to prevent duplication of effects on network retry.
- **All inbound webhook signatures must be verified before processing**: processing unauthenticated webhook payloads allows any actor to forge events and inject fraudulent state changes.
- **Replay protection is required for all inbound webhooks**: a nonce, timestamp check, or event ID deduplication store must prevent re-processing of replayed events.
- **Credentials must never be in source code, container images, or hardcoded configuration**: use secrets management (Vault, AWS Secrets Manager, GCP Secret Manager) with rotation support.
- **Sandbox testing is required before production integration**: every integration must be validated against the provider's sandbox environment with realistic test cases before any live credentials are used.
- **Reconciliation must be designed and scheduled**: any integration that transfers state, data, or money must have a reconciliation job that detects and alerts on drift between system state and provider state.
- **Circuit breakers are required for integrations on the critical path**: an unavailable external provider must not cascade into the unavailability of the consuming service.

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

## Risk Escalation Rules
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

### Anti-Examples

| Integration Pattern | Problem | Corrected Approach |
|---|---|---|
| `requests.get(url)` — no timeout | Thread holds indefinitely on provider unavailability | `requests.get(url, timeout=(3.0, 30.0))` — connection timeout 3s, read timeout 30s |
| Retry all failures immediately, no limit | 500 error retried 1000x/minute — provider bans account | Exponential backoff: 1s, 2s, 4s, 8s, 16s + jitter; max 5 retries |
| Process webhook before signature check | Forged events inject fraudulent state | Verify `X-Stripe-Signature` HMAC first; reject 401 on failure; then process |
| API key in `config/secrets.yaml` in source repo | Credential leak via git history | Retrieve from Vault or AWS Secrets Manager at runtime; rotate on exposure |
| No reconciliation for payment webhooks | Missed `payment.succeeded` event = unconfirmed order forever | Hourly reconciliation job compares order status against provider payment status |

## Failure Modes
- **Unbounded retries amplify incidents**: a 5-second provider outage produces 50,000 retry requests per minute — the provider interprets it as a DDoS and bans the integration account.
- **Missing idempotency duplicates payment**: a payment request times out, the client retries without an idempotency key — the customer is charged twice; chargeback and reconciliation follow.
- **Unsigned webhook forged**: an attacker sends a crafted `payment.succeeded` event — order fulfillment is triggered without a real payment.
- **OAuth token invalidated mid-request**: a token refresh invalidates the token currently used by another in-flight request — all requests using the old token fail simultaneously.
- **Rate limit exceeded, no backoff**: an import job issues 10,000 requests in 60 seconds against a provider with a 100 requests/minute limit — all requests after the 100th fail with 429 and retry without delay, compounding the problem.
- **No reconciliation reveals drift**: a webhook delivery failure goes undetected — order state diverges from payment state for 72 hours until a user reports a discrepancy.
- **Credential expires during peak traffic**: an API key with no rotation monitoring expires — the integration silently fails for all users until an operator manually rotates the key.
- **Webhook body parsed before HMAC**: the web framework pretty-prints the JSON before HMAC computation — the signature never matches the provider's signature; all webhooks are rejected.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return an integration design with:
- **Provider contract**: API version, deprecation status, rate limits, quota, and sandbox availability.
- **Authentication design**: Credential type, storage location, rotation schedule, and rotation automation.
- **Resilience configuration**: Timeout values, retry policy, backoff algorithm, circuit breaker thresholds.
- **Idempotency design**: Key strategy, scope, storage, TTL, and duplicate-request handling.
- **Inbound webhook security**: Signature algorithm, verification implementation, replay protection mechanism.
- **Reconciliation plan**: Job schedule, drift threshold, alert owners, and remediation procedure.
- **Credential lifecycle plan**: Current storage, rotation schedule, expiry monitoring, and automated rotation if applicable.
- **Test obligations**: Sandbox tests (normal, timeout, rate-limit, signature-failure cases), idempotency tests, reconciliation tests.
- **Observability**: Metrics (success rate, latency, retry rate, circuit state, reconciliation drift), alert thresholds, and on-call routing.

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

## Completion Criteria
Integration changes are ready when all outbound calls have explicit timeouts, bounded retries with backoff, and idempotency keys; all inbound webhooks verify HMAC signatures over raw bodies and deduplicate events; all credentials are in secrets management with rotation schedules; circuit breakers are configured for critical-path integrations; sandbox validation covers normal and failure paths; a reconciliation job is scheduled with alerting; and the test suite covers timeout, rate-limit, signature-failure, and duplicate-event scenarios.
