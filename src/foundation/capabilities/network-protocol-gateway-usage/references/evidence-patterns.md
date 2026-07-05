# Network Protocol Gateway Evidence Patterns

## Required Evidence

- Hop map: client, DNS, CDN/WAF, load balancer, ingress/proxy, app, upstream, and response path.
- Config: gateway route, timeout, retry, header, TLS, body limit, buffering, and cache settings.
- Probe: `curl`, `openssl s_client`, `dig`, gateway config test, synthetic request, or provider diagnostic.
- Logs: request id, gateway status, upstream status, duration breakdown, retry count, and trace id.
- Rollback: DNS TTL, config revert, certificate rollback, route disable, or feature flag.

## Tool Permission Boundary

Classify commands as read-only (`dig`, `curl` safe GET, `openssl s_client`, config syntax check, log query) or state-mutating (DNS change, certificate upload, gateway reload, ingress apply, CDN purge). State whether probes hit production and whether requests are idempotent.

## Handoff Shape

```
Network Protocol Gateway Record
- Network surface:
- Hop chain:
- Timeout/retry contract:
- Header/security contract:
- Validation:
- Residual risk:
```

## Blocking Conditions

Block completion when timeout changes lack hop-chain evidence, untrusted proxy headers are accepted, TLS rollout lacks renewal/rollback, gateway retries non-idempotent writes, or a 5xx diagnosis lacks logs from the emitting hop.
