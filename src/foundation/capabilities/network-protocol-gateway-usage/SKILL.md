---
name: network-protocol-gateway-usage
description: Use when HTTP, TLS, DNS, proxy, load balancer, CDN, ingress, Nginx, Envoy, HAProxy, Cloudflare, timeout chain, header, WebSocket, or gateway behavior needs evidence-backed design or debugging.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "133"
changeforge_version: 0.1.0
---

# Mission

Make network and gateway behavior explicit across clients, DNS, TLS, proxies, CDNs, load balancers, ingress, service mesh, upstream services, timeouts, retries, headers, and observability. A 502, 503, 504, CORS, WebSocket, or TLS symptom is not resolved until the full hop chain and protocol contracts are understood.

# When To Use

Use when a change touches Nginx, Envoy, HAProxy, Apache, Cloudflare, Fastly, CloudFront, ALB/NLB, Kubernetes ingress, API gateway, service mesh, TLS certificates, DNS, HTTP versions, proxy headers, `X-Forwarded-*`, `Forwarded`, CORS, WebSocket upgrades, gRPC, keepalive, connection pooling, timeout/retry chains, rate limits, gateway auth, request size limits, compression, caching at gateway, or 502/503/504 incident diagnosis.

# Do Not Use When

Do not use for ordinary REST DTO field changes, internal function calls, or application-level API semantics where no network/gateway/protocol behavior changes. Use `api-contract-design` for operation-level API behavior and `integration-change-builder` for external provider business contracts.

# Non-Negotiable Rules

- Map every hop: client, DNS, CDN, WAF, load balancer, ingress, proxy, service mesh, app, upstream dependency, and response path.
- Timeout chain must be ordered intentionally: caller timeout >= gateway timeout >= upstream timeout when the caller needs a gateway response; retries must fit inside the end-to-end deadline.
- Retry policy must avoid amplification: bounded attempts, backoff/jitter, idempotency awareness, and retry budget.
- Preserve and validate `Host`, scheme, client IP, request id, trace context, and auth headers across trusted proxy boundaries.
- TLS changes require certificate chain, SNI, ALPN, cipher/protocol policy, renewal path, and client compatibility evidence.
- WebSocket, streaming, SSE, and gRPC require protocol-specific upgrade, idle timeout, buffer, and HTTP/2 behavior.
- Gateway request/response body limits, header limits, compression, buffering, and chunking must be explicit.
- Gateway logs and metrics must identify the failing hop, upstream status, duration, retry count, and correlation id.
- Security-sensitive headers, CORS, cookies, and auth forwarding must route through security review.
- Do not mask upstream defects by raising gateway timeouts without capacity, SLO, and backpressure evidence.

# Industry Benchmarks

Anchor decisions against RFC 9110/9111/9112 HTTP semantics and caching, RFC 8446 TLS 1.3, RFC 7239 Forwarded headers, W3C Trace Context, OpenTelemetry semantic conventions, Nginx/Envoy/HAProxy gateway documentation, Kubernetes ingress guidance, Cloudflare/Fastly/CloudFront edge behavior, OWASP API Security and TLS cheat sheets, and Google SRE guidance on cascading failure and retry amplification.

# Selection Rules

Select when protocol or gateway behavior is the central risk: timeout chains, proxy headers, TLS, DNS, CDN/edge, ingress, WAF, load balancing, streaming, WebSockets, gRPC, or 502/503/504 diagnosis. Pair with `reliability-observability-gate` for SLO/backpressure, `security-privacy-gate` for CORS/auth/header/TLS trust boundaries, `integration-change-builder` for upstream contracts, and `observability` for hop-level metrics.

# Risk Escalation Rules

Escalate to `security-privacy-gate` for auth header forwarding, client IP trust, CORS, cookies, TLS downgrade, WAF bypass, or public exposure. Escalate to `reliability-observability-gate` for timeout changes, retry chains, 5xx incidents, connection pool saturation, or CDN/origin failover. Escalate to `delivery-release-gate` for DNS, certificate, ingress, or load balancer rollout. Escalate to `api-contract-design` when protocol changes alter client-visible API semantics.

# Critical Details

- **504 is a chain symptom.** The gateway that emits 504 may not be the slow component; inspect upstream connect time, header time, response time, and caller deadline.
- **Timeout order creates behavior.** If CDN timeout is shorter than origin, users see 524/504 while the origin keeps working; if app timeout is shorter, gateway sees reset/502.
- **Retries can cause outages.** Gateway retries on non-idempotent POST or on every 5xx can multiply load during partial failure.
- **Trusted proxy boundary matters.** Accept `X-Forwarded-For` only from known proxies; otherwise attackers spoof client IP, scheme, or host.
- **HTTP/2 and gRPC differ from HTTP/1.1.** Connection reuse, stream limits, trailers, and idle timeouts need explicit config.
- **WebSocket and streaming need buffering controls.** Proxy buffering, idle timeout, and upgrade headers can break long-lived connections.
- **DNS has deployment latency.** TTL, negative caching, split-horizon, and resolver behavior affect rollback.
- **CDN cache and gateway auth interact.** Public/shared edge caches must not store per-user responses.

# Failure Modes

- **504 timeout chain:** Cloudflare timeout is shorter than Nginx/app/upstream work; clients get 504 while app keeps processing.
- **Retry amplification:** load balancer retries every slow request, doubling origin load and causing a cascade.
- **Spoofed client IP:** app trusts unvetted `X-Forwarded-For`, bypassing rate limits or geo policy.
- **TLS/SNI mismatch:** certificate works for one hostname but fails for another after DNS cutover.
- **WebSocket disconnect:** proxy idle timeout or missing upgrade header closes connections every 60 seconds.
- **gRPC broken by HTTP/1.1 ingress:** trailers or HTTP/2 are not preserved.
- **Header/body limit mismatch:** CDN allows larger request than ingress, producing intermittent 413/502.
- **CORS wildcard with credentials:** browser blocks or exposes data depending on misconfigured headers.
- **CDN origin cache leak:** authenticated response cached at edge because `Cache-Control` or `Vary` was wrong.

# Output Contract

Return a Network Protocol Gateway Record with:

- `network_surface` (DNS, TLS, CDN, WAF, load balancer, ingress, proxy, service mesh, app upstream, streaming/gRPC/WebSocket)
- `hop_chain` (client through origin and back, with trust boundaries)
- `protocol_contract` (HTTP version, TLS/SNI/ALPN, headers, body limits, compression, buffering, upgrade behavior)
- `timeout_retry_contract` (connect/read/write/idle timeouts, caller deadline, retry attempts, backoff, idempotency)
- `header_identity_contract` (`Host`, scheme, client IP, request id, trace context, auth/cookie forwarding)
- `security_contract` (CORS, cookies, WAF, TLS policy, cacheability, trusted proxies)
- `observability_contract` (gateway/upstream status, latency breakdown, retry count, trace id, log fields, alerts)
- `decision_record` (change made, alternatives rejected, capacity and SLO rationale)
- `validation_commands` (curl/openssl/dig/kubectl/nginx/envoy config test, synthetic request, log query, or not-run disclosure)
- `residual_risk` (untested client, region, resolver, edge provider, or production traffic pattern)

# Quality Gate

1. Hop chain and trust boundaries are mapped.
2. Timeout and retry chain is bounded, ordered, and idempotency-aware.
3. TLS, DNS, HTTP version, headers, and body/stream limits are explicit.
4. Client identity and trace headers are accepted only across trusted proxies.
5. Security-sensitive gateway behavior is reviewed.
6. Logs and metrics can identify the failing hop and correlate to app traces.
7. Rollout and rollback are defined for DNS, certificate, CDN, ingress, or gateway config.
8. Validation covers at least the changed protocol path or discloses why not.
9. Residual risk names untested clients, regions, providers, or live-load behavior.

# Used By

integration-change-builder, reliability-observability-gate, security-privacy-gate, delivery-release-gate, backend-change-builder

# Handoff

Hand off to `api-contract-design` for client-visible operation semantics, `web-security` for browser/CORS/cookie/header risk, `degradation-circuit-breaking` for fallback and overload, `observability` for telemetry implementation, and `delivery-release-gate` for gateway/DNS/certificate rollout.

# Completion Criteria

Network/gateway work is complete when the hop chain is explicit, timeouts and retries are bounded, protocol/header/TLS behavior is validated, security boundaries are reviewed, observability identifies the failing hop, and rollout/rollback risk is owned.
