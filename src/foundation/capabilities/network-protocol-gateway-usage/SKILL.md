---
name: network-protocol-gateway-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when HTTP/TLS/DNS, proxies, ingress, headers, timeout chains, WebSocket, or gateways change; skip without network-edge impact."
---

# network-protocol-gateway-usage

## Registry Trigger

**Use when**

- Nginx Envoy HAProxy Cloudflare Fastly CloudFront ALB NLB
- ingress API gateway service mesh WAF CDN reverse proxy load balancer
- TLS DNS SNI ALPN
- HTTP proxy header X-Forwarded-For Forwarded Host CORS
- WebSocket SSE gRPC timeout-chain
- 502 503 504 retry-amplification upstream-status edge origin trace context
- path-rewrite cache-key TTL invalidation purge stale-behavior per-user data health check origin shielding

**Do not use when**

- no task-local network protocol gateway usage decision is required

## Skill Role

Trace client-to-origin behavior across name resolution, transport, proxies, retries, headers, protocol upgrades, caching, and telemetry. Own hop-chain deadline and retry ceilings; `degradation-circuit-breaking` owns application/dependency resilience and out-of-chain local deadlines, leaving no shared or unowned boundary.

## High-Value Rules

- Map only affected client-to-origin hops, excluding those proven irrelevant to the symptom or change.
- Derive the gateway-owned caller, gateway, and upstream deadline and retry ceilings from the end-to-end budget, cancellation behavior, and amplification risk. Degradation consumes those ceilings without redefining them.
- Preserve host, scheme, client identity, request context, trace context, and authorization only across trusted proxies.
- Validate forwarded values before using them as authority.
- When transport security changes, verify certificate chain, endpoint identity, negotiation policy, renewal, and affected client compatibility.
- Select upgrade, idle, buffering, framing, and connection controls from the actual streaming, WebSocket, event-stream, RPC, or protocol behavior.
- Define body, header, compression, buffering, and chunking bounds from accepted payloads, resource limits, and abuse risk.
- Require telemetry that identifies the failing hop and relevant upstream result, duration, retry, and correlation context when diagnosis or operation depends on it.

## Anti-Patterns

- A gateway error identifies the reporting hop, not necessarily the slow or failed component.
- Raising a timeout without capacity, cancellation, and backpressure evidence can preserve work after callers have left.
- Accepting forwarded identity from an untrusted peer lets a client spoof origin, scheme, host, or authority.
- Shared caching of authorization-dependent responses can cross user or tenant boundaries.

## Stop Conditions

Escalate forwarded identity, authorization, cookies, transport downgrade, edge bypass, or public exposure to `security-privacy-gate`.
Escalate saturation or failover to `reliability-observability-gate`.
Route application/dependency fallback, bulkhead, circuit, recovery, and local deadlines outside a gateway chain to `degradation-circuit-breaking`.
Escalate DNS, certificate, ingress, or load-balancer rollout to `delivery-release-gate`.
Escalate protocol behavior that changes the client contract to `api-contract-design`.

## Output Contract

- Network Gateway Record: map surfaces, hops, protocol, timeouts, retries, trusted headers, security, and observability; include decisions, validation commands, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | timeout retry header TLS cache or streaming mechanisms remain undecided | current hop contracts and provider policy select one mechanism | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | gateway changes affect hop trust deadlines retries TLS or protocol limits | no network hop or gateway behavior changes | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | routing timeout TLS or failing-hop claims need representative proof | fresh config probes and correlated telemetry prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
