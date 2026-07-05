# Network Protocol Gateway Checklist

- Map client, DNS, CDN/WAF, load balancer, ingress/proxy, service mesh, app, upstream, and response path.
- State trust boundaries for `Host`, scheme, client IP, request id, trace context, auth, cookies, and forwarded headers.
- Compare caller, CDN/WAF, load balancer, proxy, app, and upstream connect/read/write/idle timeouts.
- Bound retries by method, idempotency, attempt count, backoff, retry budget, and end-to-end deadline.
- Record TLS certificate chain, SNI, ALPN, protocol/cipher policy, renewal path, and rollback.
- Record DNS TTL, split-horizon or resolver behavior, negative cache risk, rollout order, and rollback.
- Record body/header limits, buffering, compression, streaming, WebSocket, SSE, or gRPC behavior.
- Review CDN cache key, `Vary`, `Cache-Control`, cookies/auth headers, purge/invalidation, stale behavior, and per-user data safety.
- Review WAF bypass rules, origin shielding, health checks, origin auth, and failover.
- Validate with the smallest command or artifact that can fail for the changed hop, then state what it does and does not prove.
