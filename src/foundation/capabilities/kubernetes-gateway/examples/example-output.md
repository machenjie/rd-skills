# Example Output

```markdown
## Kubernetes Runtime Decision

Boundary: a stateless API workload and its internal service gain a new external route.

Workload and health:
- The selected controller matches long-running replaceable processes with no stable local storage.
- Startup gates initialization, readiness controls traffic and drain, and liveness observes a local unrecoverable process failure.
- Requests, limits, scaling, disruption, and placement use the current load and failure-domain evidence; production headroom remains unproved.

Identity and traffic:
- A workload-specific identity receives the changed permissions and network paths.
- The route names listener, host/path, backend, TLS/auth, timeout, tenant exposure, and external DNS/edge owner.
- Secret values remain outside rendered source; the release identity records their version references.

Rollout:
- Rendered workload, image digest, config, route, policy, and target namespace share one release identity.
- Mixed-version compatibility, watch signals, stop authority, route reversal, and forward recovery are named.

Evidence limit:
- Current render and policy checks prove inspected intent; live admission, edge propagation, traffic, and capacity await the authorized release gate.
```
