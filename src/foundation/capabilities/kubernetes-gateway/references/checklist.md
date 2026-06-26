# Kubernetes Gateway Checklist

Use this reference after the main skill selects `kubernetes-gateway` for a concrete shared or production Kubernetes, Gateway API, Helm, GitOps, RBAC, NetworkPolicy, secret, rollout, or rollback decision.

## Operational Maturity Gate

- Confirm Kubernetes is justified by scale, reliability, scheduling, networking, or platform constraints that a simpler managed runtime cannot satisfy.
- Name the platform owner, application owner, release owner, on-call path, incident runbook, deployment pipeline, rollback procedure, and post-release watch owner.
- Confirm centralized logs, metrics, traces or trace context, alert routing, secret management, NetworkPolicy enforcement, and policy-as-code are available.
- If these are absent, recommend a simpler deployment target or block Kubernetes adoption until ownership and evidence exist.

## Workload Contract

| Concern | Required decision | Evidence to capture |
| --- | --- | --- |
| Workload type | Deployment, StatefulSet, DaemonSet, Job, or CronJob. | Lifecycle, restart policy, storage, concurrency, and scheduling rationale. |
| Replicas | Initial replica count and HA target. | Traffic baseline, RTO/RPO need, cost constraint, and scale plan. |
| Shutdown | `terminationGracePeriodSeconds`, preStop, drain behavior. | In-flight request/job behavior and maximum safe drain time. |
| Storage | PVC, emptyDir, config volume, secret volume, or no volume. | Persistence need, backup/restore owner, and StatefulSet/PVC rollback impact. |
| Scheduling | node affinity, taints/tolerations, topology spread, priority class. | Zone/node placement intent and failure-domain risk. |
| Image | immutable tag or digest, pull policy, registry, provenance. | Tag policy, image scan/provenance handoff, and previous rollback image. |

## Probe Design

- Liveness: checks process responsiveness only; avoid external dependencies. Failing liveness restarts the container.
- Readiness: checks whether traffic can be served; it may include dependency readiness when failure should remove the pod from load balancing.
- Startup: protects slow init before liveness starts; use when warmup or migrations exceed normal liveness windows.
- Graceful shutdown: readiness should fail before termination drains traffic.

| Anti-pattern | Failure | Corrective action |
| --- | --- | --- |
| Liveness calls DB/cache. | Dependency maintenance restarts every pod. | Move dependency check to readiness. |
| Readiness always returns 200. | Broken pods continue receiving traffic. | Gate on app readiness, config, warmup, and needed dependencies. |
| No startup probe for slow boot. | Pods restart before initialization completes. | Add startup probe with bounded failure window. |
| Same endpoint for all probes. | Traffic and restart semantics cannot diverge. | Separate `/livez`, `/readyz`, and `/startupz` or equivalent behavior. |

## Resources, Scaling, And Availability

| Concern | Kubernetes setting | Review rule |
| --- | --- | --- |
| Scheduler placement | CPU/memory requests | Set for every container from P95 observed usage, forecast, or VPA recommendation. |
| Latency sensitivity | CPU limit | Avoid tight CPU limits for latency-sensitive services unless throttling impact is known. |
| OOM risk | Memory request/limit | Explain QoS target; critical services often need request and limit aligned. |
| Horizontal scale | HPA metric and target | Use CPU/memory or custom metric with requests present; state target and alert. |
| Event scale | KEDA ScaledObject | State trigger type, threshold, cooldown, and scale-to-zero behavior. |
| Maintenance safety | PodDisruptionBudget | Use `minAvailable` or `maxUnavailable` for HA workloads; justify skip. |
| Failure domain | topologySpreadConstraints | Spread across zones/nodes where availability requires it. |

## Traffic And Gateway Review

- Service type: ClusterIP, LoadBalancer, NodePort, headless, or ExternalName with reason.
- Gateway/Ingress: host, path, method, TLS secret/cert manager, backend ref, timeout, body size, retry, auth, CORS, and rate limit.
- Exposure: internal, partner, internet, or tenant-specific; state cloud account/project, namespace, DNS/CDN/WAF/load balancer boundary, and audit owner.
- Compatibility: old and new routes coexist through rollout and rollback windows.
- Rollback: route, DNS, CDN, WAF, TLS cert, and service selector reversal are explicit.

## Security, Identity, And Secret Review

- Use a dedicated ServiceAccount per workload; disable default token automount unless needed.
- Bind minimum Role/ClusterRole permissions; cluster-level RBAC needs explicit escalation.
- Use cloud workload identity such as IRSA or Workload Identity instead of static cloud keys.
- Apply namespace default-deny NetworkPolicy, then add explicit ingress and egress allow rules.
- Set pod/container security context: non-root, no privilege escalation, dropped capabilities, read-only root filesystem where feasible, seccomp/AppArmor where supported.
- Use ExternalSecrets, Sealed Secrets, CSI Secret Store, Vault, or platform secret manager; avoid committed plaintext and secret-like `values.yaml` keys.
- Ensure rendered manifests and values are scanned for passwords, tokens, private keys, client secrets, and credential-looking literals.

## Helm And GitOps Release Controls

- `Chart.yaml`: chart version and `appVersion` match the release intent.
- Dependencies: `helm dependency build` uses locked dependencies from `Chart.lock`.
- Values: safe defaults only; environment overlays are minimal and do not fork chart behavior.
- Schema: `values.schema.json` validates required values, types, enums, resource shape, and unsafe defaults.
- Render: `helm template` succeeds for every supported environment values file.
- Lint and validate: `helm lint`, rendered manifest validation such as kubeconform/kubeval, and policy-as-code pass.
- Diff: `helm diff` or GitOps rendered diff is attached to review.
- Upgrade: production uses `--atomic --wait --timeout` or equivalent GitOps health/sync safeguards.
- CRDs: ownership, install/upgrade ordering, compatibility, and rollback limitations are documented.
- Hooks: hook jobs are idempotent, bounded by timeout, use scoped RBAC, and define delete/rerun behavior.

## Rollout And Rollback Review

| Strategy | Use when | Required rollback evidence |
| --- | --- | --- |
| RollingUpdate | Standard stateless service with correct readiness. | previous image, config/secret version, route and schema compatibility. |
| Canary | High-risk or high-traffic production release. | traffic step plan, metric threshold, automated/manual rollback owner. |
| Blue-green | Zero-downtime cutover with parallel capacity. | traffic switch back, shared database compatibility, config parity. |
| Recreate | Dev/test, singleton, or incompatible stateful change. | downtime window, user impact, and restore/forward-fix path. |

Rollback scope must cover image, ConfigMap, Secret source/version, Gateway/Ingress/DNS/CDN/WAF, Service selector, database schema, feature flag, CRD, hook job, provider-side configuration, and external dependency state where changed.

## Observability And Validation Evidence

- Post-deploy watch: request rate, error rate, p95/p99 latency, saturation, pod restarts, OOMKills, CrashLoopBackOff, HPA/KEDA events, readiness failures, and Gateway/Ingress error metrics.
- Smoke test: name command, target route, auth mode, expected status/body, and rollback trigger.
- Validation ledger: command, output summary, exit code, report/artifact path, covered files, and freshness relative to final manifest/chart edit.
- Evidence limits: rendered manifests do not prove live admission, provider-side DNS/CDN/WAF behavior, production capacity, canary success, or secret rotation unless separately verified.
