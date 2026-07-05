# Example Output

## Input Scenario

Users see intermittent 504s through Cloudflare and Nginx for a report export endpoint. The app keeps processing the export after the client disconnects.

## Selected Capability

`network-protocol-gateway-usage`

## Decision Record

- Network surface: Cloudflare edge, Nginx ingress, backend app, report database.
- Hop chain: browser -> Cloudflare -> Nginx -> app -> database -> app -> Nginx -> Cloudflare.
- Decision: keep the synchronous route below gateway timeout, move long exports to an async operation, and set app deadline shorter than gateway read timeout.
- Rejected shortcut: raising Nginx timeout alone would leave Cloudflare timeout and origin load unresolved.

## Evidence Checklist

- Cloudflare, Nginx, and app timeouts compared.
- Upstream response duration and gateway status logs inspected.
- Client request id mapped to app trace.
- Retry behavior checked for non-idempotent export creation.
- Rollback path for ingress config named.

## Validation Commands

```
curl -v --max-time 30 https://example.com/reports/export
nginx -t
grep "$REQUEST_ID" /var/log/nginx/access.log
```

## Residual Risk

Cloudflare regional behavior and live peak export load were not reproduced locally. Owner: SRE. Follow-up trigger: 504 rate alert after deployment.

## Handoff Summary

The 504 was treated as a timeout-chain and workload-shape problem. The fix avoids retry amplification and preserves gateway deadlines.
