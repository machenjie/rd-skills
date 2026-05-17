# Kubernetes Gateway Checklist

- Confirm Kubernetes is justified by platform maturity and ownership.
- Define workload type, service account, security context, and namespace assumptions.
- Define config and secret sources without embedding secret values.
- Set resource requests, limits, scaling, and disruption expectations.
- Define readiness, liveness, and startup probes from real health signals.
- Define service, ingress or gateway hosts, paths, TLS, and timeouts.
- Include network policy and exposure review where relevant.
- Define rollout, rollback, post-deploy verification, and observability.
