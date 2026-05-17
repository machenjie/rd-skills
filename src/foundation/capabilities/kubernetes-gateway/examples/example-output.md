# Example Output

```markdown
## Kubernetes Gateway Plan

Maturity decision:
- Use existing platform namespace with owned CI deployment and observability.

Workload:
- Deployment for stateless API.
- Non-root security context and dedicated service account.
- Requests and limits sized from current staging load.

Traffic:
- Service exposes HTTP internally.
- Gateway routes api.example.com/v2 to the service with TLS and request timeout.

Health:
- Readiness checks dependency-backed health.
- Liveness checks process recovery only after startup completes.

Rollout:
- Rolling update with canary verification and rollback trigger on error-rate SLI.
```
