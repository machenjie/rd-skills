# Kubernetes Gateway Evidence Patterns

## Required Evidence

- Source boundary: manifests, Helm chart, values overlays, GitOps app, CRDs/hooks, namespace, Service, Ingress/Gateway, RBAC, NetworkPolicy, secrets/config, pipeline, runbook, dashboard, and owner.
- Render evidence: `helm lint`, `helm template`, values schema, rendered manifest validation, policy-as-code result, diff, artifact path, exit code, and freshness after final edit.
- Traffic/security evidence: host/path/TLS/auth/timeouts/rate limits, public/internal exposure, DNS/CDN/WAF/load balancer boundary, ServiceAccount/RBAC diff, NetworkPolicy allowlist, secret source, and rollback step.
- Reliability evidence: probe semantics, requests/limits baseline, HPA/KEDA/VPA metric, PDB/topology decision, post-deploy watch metric, alert owner, and capacity evidence limit.
- Release/rollback evidence: rollout strategy, atomic/wait/GitOps sync behavior, image/config/secret/route/schema/CRD/hook rollback scope, forward-fix owner, and stop condition.
- Graph/memory/execution evidence: inspected paths, accepted/rejected prior deploy claims, generated report/dist freshness, final validation order, and unverified provider/cluster behavior.

## Tool Permission Boundary

Classify actions as read-only source inspection, local render/report write, local policy validation, cluster dry-run, GitOps sync, Helm/Kubernetes live mutation, cloud/DNS/CDN/WAF mutation, secret read/write, or rollback. State sandbox/approval state, target context/namespace/account, write scope (`HOME`, source tree, report artifacts, `dist/`, cluster, cloud provider), rollback/forward-fix path, and secret redaction rule.

## Handoff Shape

```markdown
Kubernetes Gateway Evidence Record
- Source boundary:
- Render/policy proof:
- Traffic/security proof:
- Reliability proof:
- Release/rollback proof:
- Graph/memory/execution freshness:
- Tool permission boundary:
- Validation:
- What remains unproved:
- Residual operational risk:
```

## Blocking Conditions

Block completion when live mutation lacks dry-run/rendered diff and rollback, public exposure lacks owner/TLS/auth/blast-radius review, secrets are present in committed values/manifests, probes/resources/PDB are copied without service-specific evidence, CRD/hook rollback is unclear, or stale graph/memory/deploy claims are reused without current-source confirmation.
