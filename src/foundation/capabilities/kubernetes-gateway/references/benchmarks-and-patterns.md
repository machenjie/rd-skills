# Kubernetes Runtime Decision Patterns

These patterns compare workload, identity, traffic, capacity, and rollout decisions for the changed cluster boundary.

## Workload And Controller Fit

| Runtime concern | Decision focus | Failure to expose |
| --- | --- | --- |
| Process identity and completion | long-running, singleton, per-node, scheduled, finite, or stateful lifecycle | duplicate work, lost completion, or wrong restart behavior |
| Storage and stable identity | attachment, ownership, failover, fencing, detach/rebind, and restore | split ownership, stale attachment, or unrecoverable state |
| Health and termination | startup, readiness, liveness, drain, grace, and in-flight work | restart storm, early traffic, or dropped work |
| Capacity and placement | requests, limits, scaling signal, disruption, topology, priority, and queue pressure | throttling, eviction, correlated failure, or unsafe scale-down |
| Identity and reachability | workload identity, namespace, permissions, secret/config source, ingress and egress | broad privilege, credential leak, or unintended network path |
| Traffic exposure | listener, route, backend, TLS/auth, timeout/retry/body/rate policy, tenant and edge ownership | public expansion, incompatible routes, or ambiguous reversal |
| Rollout state | image/config/secret/route/policy identity, mixed versions, custom resources, hooks, external state | partial rollout or rollback that leaves other surfaces changed |

## Selection Notes

- Choose supported resources and controls from the current cluster API, controller behavior, platform policy, and workload consequence; avoid a vendor or standards catalog in task context.
- Separate rendered intent from admission, defaulting, controller reconciliation, load balancer, DNS/edge, and runtime state.
- Select disruption, placement, isolation, scaling, and exposure mechanisms when the affected workload risk triggers them, with an explicit proof limit for live cluster behavior.
- Route image contents to `containerization`, pipeline mutation to `ci-cd`, data change execution to `data-migration-design`, and final release authority to `delivery-release-gate`.
