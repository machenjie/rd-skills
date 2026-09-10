# Network Protocol Gateway Benchmarks And Patterns

- RFC 9110/9111/9112 for HTTP semantics, caching, and HTTP/1.1 syntax.
- RFC 8446 for TLS 1.3 and certificate-chain behavior.
- RFC 7239 for `Forwarded` headers and W3C Trace Context for correlation.
- OpenTelemetry semantic conventions for HTTP server/client and proxy spans.
- Nginx, Envoy, HAProxy, Kubernetes ingress, Cloudflare, Fastly, CloudFront, ALB/NLB, and service mesh documentation.
- OWASP API Security and TLS guidance.

## Timeout Pattern

Derive explicit timeout budgets for the affected hops in the actual request chain from current upstream behavior and the end-to-end deadline:

| Hop | Timeout fields | Evidence |
| --- | --- | --- |
| Client | request deadline, retry budget | client config |
| CDN/WAF | edge/origin timeout, cache behavior | provider rule |
| Load balancer | idle/connect timeout | LB config |
| Ingress/proxy | connect/read/send timeout | config test |
| App | server/request timeout | app config |
| Upstream | client timeout and retry | source/config |

## Header Trust Pattern

At the first trusted ingress, remove inbound client-identity headers. Set canonical client identity only from independently authenticated ingress evidence. Ignore or deny absent or invalid identity according to documented policy. Each subsequent trusted proxy preserves or appends identity according to the documented hop model, and downstream services accept forwarded identity only from authenticated or allowlisted proxies.

## Streaming Pattern

For WebSocket, SSE, and gRPC, verify upgrade or HTTP/2 behavior, buffering disabled where needed, idle timeout longer than expected silence, and backpressure behavior on slow clients.
