# Kubernetes Gateway Benchmarks And Patterns

## Baseline Standards

- Use Kubernetes upstream API behavior, Gateway API, Helm chart best practices, GitOps rendered-diff discipline, CIS Kubernetes Benchmark, NSA/CISA Kubernetes Hardening Guide, and Kubernetes Pod Security Standards as review anchors.
- Treat pinned platform versions, controller versions, admission policies, and chart dependencies as project baselines; update this capability before relying on obsolete Kubernetes, Helm, Gateway API, or policy-tool assumptions.
- Prefer a simpler managed runtime when platform ownership, on-call, rollback, observability, secret management, and NetworkPolicy enforcement are not ready.

## Design Patterns

- Separate liveness, readiness, and startup semantics; liveness must not depend on external services.
- Size requests, limits, and autoscaling from observed data, forecast, or explicit residual risk; avoid copied values.
- Use dedicated ServiceAccounts, least-privilege RBAC, default-deny NetworkPolicy, non-root security context, and approved secret sources.
- Validate Helm/GitOps changes through schema, lint, template/render, diff, policy checks, and CRD/hook ordering before release.
- Keep Gateway/Ingress rollback explicit across route, DNS, CDN, WAF, TLS secret, Service selector, and backend compatibility.
- Pair rollout strategy with watch metrics and stop conditions; canary or blue-green requires traffic step ownership and rollback trigger.

## Deviation Record

```markdown
Kubernetes Gateway Deviation
- Rule:
- Reason:
- Scope:
- Owner:
- Expiration or cleanup trigger:
- Validation proving the exception is bounded:
```
