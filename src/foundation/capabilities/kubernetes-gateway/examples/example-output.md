# Example Output

```markdown
## Kubernetes Gateway Plan

mode_selected:
- Helm/GitOps release with traffic exposure review.

boundaries_inspected:
- Workload, namespace, Service, Gateway route, TLS, ServiceAccount/RBAC, NetworkPolicy, ExternalSecrets, Helm chart, rollout, rollback, and post-deploy watch.

workload_contract:
- Deployment for stateless API.
- Non-root security context and dedicated service account.
- Requests and limits sized from current staging load.
- PDB `minAvailable: 1` and zone topology spread required.

traffic_security:
- Service exposes HTTP internally.
- Gateway routes api.example.com/v2 to the service with TLS and request timeout.
- NetworkPolicy allows only Gateway namespace ingress and approved database egress.

health_resources_scaling:
- Readiness checks dependency-backed health.
- Liveness checks process recovery only after startup completes; it does not call the database.
- HPA scales on CPU and request latency saturation signal.

release_validation:
- `helm lint`, `helm template`, values schema validation, rendered manifest validation, and policy checks must pass with current output and exit code recorded.

rollback_plan:
- Rolling update with canary verification and rollback trigger on error-rate SLI.
- Rollback covers image, values/config, ExternalSecret version, Gateway route, and schema compatibility; CRD/hook scope is not changed.

residual_risk:
- Live DNS/CDN behavior and production capacity remain unproven until staged release watch.
```
