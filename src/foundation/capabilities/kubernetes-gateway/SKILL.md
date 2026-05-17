---
name: kubernetes-gateway
description: Defines Kubernetes workload, service, ingress or gateway, probes, resources, rollout, and rollback only when operational maturity justifies Kubernetes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "74"
changeforge_version: 0.1.0
---

# Mission

Deploy and operate Kubernetes workloads **deliberately** — defining workload type, routing contract, real health semantics, resource budgets, security posture, rollout strategy, and rollback scope — accepting Kubernetes complexity only when the team has the operational maturity to own it safely.

# When To Use

Use this capability when a change: deploys a new workload to Kubernetes (Deployment, StatefulSet, Job, CronJob, DaemonSet); modifies Ingress or Gateway API routing rules; changes liveness, readiness, or startup probe configuration; adjusts resource requests, limits, or HPA/KEDA scaling policy; modifies ServiceAccount, RBAC, or NetworkPolicy; changes rollout strategy or PodDisruptionBudget; or introduces a new service that must be reachable inside or outside the cluster.

# Do Not Use When

Do not use this capability to introduce Kubernetes for a runtime that lacks: a team member who owns platform operations; automated deployment pipeline with rollback capability; centralized logging and metrics; secret management (not in manifests); and network policy enforcement. Kubernetes is not a deployment simplification tool — it is operational complexity traded for scalability and reliability. Introducing it without operational ownership creates a higher-risk environment than the alternative.

# Non-Negotiable Rules

- **Readiness controls traffic; liveness restarts processes; startup protects slow init.** These are not interchangeable. Readiness: "is the pod ready to receive traffic?" — failing readiness removes the pod from load balancing without restarting it. Liveness: "is the pod alive and not deadlocked?" — failing liveness restarts the pod. Startup: "is the pod done initializing?" — disables liveness during slow startup to prevent premature restart loops. Never check process existence (e.g., HTTP 200 from a `/health` endpoint that always returns 200) — check real application readiness (DB connection pool ready; cache warmed; config loaded).
- **Resource requests are required on every container; limits must be set for CPU if autoscaling is used.** Without resource requests, the Kubernetes scheduler cannot make correct placement decisions; pods compete unpredictably for node resources. CPU limits cause throttling; memory limits cause OOMKill. Set CPU request = expected steady-state usage; CPU limit = peak burst allowance or omit for latency-sensitive workloads. Set memory request = memory limit (to prevent memory-overcommit-induced OOMKill surprises).
- **Secrets must not appear in manifests, environment literals, or container args.** Kubernetes Secrets in YAML manifests stored in Git are base64-encoded, not encrypted. Use: ExternalSecrets Operator (AWS Secrets Manager, GCP Secret Manager, Azure Key Vault); Sealed Secrets (Bitnami, encrypts for a specific cluster); HashiCorp Vault Agent Injector; or CSI Secret Store Driver. Never use `kubectl create secret` from CI without a sealed/external secret process.
- **Security context: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`, seccomp profile.** Apply at pod and container level. This is the Kubernetes Pod Security Standards "restricted" profile baseline. Root containers are a container escape risk. (NSA Kubernetes Hardening Guide; CIS Kubernetes Benchmark).
- **NetworkPolicy: deny-by-default; allow explicitly.** Without a NetworkPolicy, all pods can reach all other pods in the cluster. Implement a default-deny NetworkPolicy in every namespace; add allow rules only for required pod-to-pod communication. This is zero-trust network segmentation at the pod level.
- **ServiceAccount: create a dedicated ServiceAccount per workload with minimal RBAC.** The default ServiceAccount in most clusters has excessive permissions. Create a named ServiceAccount; bind only the Role with the minimum permissions required; annotate for Workload Identity (IRSA on EKS, Workload Identity on GKE) when cloud API access is needed — never mount cloud credentials as secrets.
- **Rollback scope is broader than deployment revision.** A Kubernetes rollout rollback (`kubectl rollout undo`) reverts the image. It does not revert: ConfigMaps; Secret values; database schema migrations; Ingress/Gateway rules; external service configuration. Define what must be reverted for each rollback scenario; document the procedure.

# Industry Benchmarks

Anchor against: **CIS Kubernetes Benchmark** (cisecurity.org) — cluster hardening, RBAC, network policy, secret handling, audit logging. **NSA/CISA Kubernetes Hardening Guide** (2022) — pod security, network separation, authentication, audit. **Kubernetes Pod Security Standards** (kubernetes.io/docs/concepts/security/pod-security-standards) — Privileged / Baseline / Restricted profiles; apply "restricted" as default for application workloads. **Kubernetes Gateway API** (gateway.sigs.k8s.io; NGINX/Envoy/Istio implementations) — successor to Ingress; GatewayClass, Gateway, HTTPRoute, TCPRoute; more expressive routing; traffic splitting for canary. **NGINX Ingress Controller** — widely deployed; `nginx.ingress.kubernetes.io/` annotations for timeout, rate limit, auth, CORS. **HPA (Horizontal Pod Autoscaler)** — CPU/memory based scaling; `targetAverageUtilization: 70%`; requires resource requests. **KEDA (Kubernetes Event-Driven Autoscaler, keda.sh)** — scale on Kafka consumer lag, SQS queue depth, Prometheus metrics, Cron; scales to zero for event-driven workloads. **VPA (Vertical Pod Autoscaler)** — recommends/sets resource requests based on actual usage; use in "Off" mode (recommendation only) to avoid disruptive pod restarts. **PodDisruptionBudget** — `minAvailable: 1` prevents all pods being evicted simultaneously during node drain; required for HA workloads. **Argo Rollouts / Flagger** — progressive delivery; canary analysis; automated rollback on error rate threshold. **Helm** — Kubernetes package manager; chart versioning; values.yaml override per environment; release history for rollback. **ExternalSecrets Operator** (external-secrets.io) — syncs secrets from AWS Secrets Manager / GCP / Azure Key Vault into Kubernetes Secrets; refresh interval; rotation without restart via `reloadOnChange`. **Prometheus + Kube-state-metrics** — pod/container metrics; HPA decisions; alerting on OOMKill, CrashLoopBackOff, pod restart rate.

### Probe Design Rules

```
Liveness probe:
  - Check application heartbeat (not just process alive)
  - Lightweight: do not call external dependencies (DB, cache)
  - If liveness calls DB and DB is down: all pods restart; cascading failure
  - initialDelaySeconds: must be > startup time (or use startupProbe instead)
  - failureThreshold × periodSeconds = max tolerable hung duration before restart

Readiness probe:
  - Check that the pod can serve traffic:
      HTTP: return 200 only when DB connection pool ready + config loaded + warmup done
      TCP: port open
      Exec: process-specific check
  - MAY call external dependencies (DB, cache) — failing readiness removes from LB without restart
  - Appropriate for: dependency unavailability, ongoing shutdown, warmup pending

Startup probe (use when init > initialDelaySeconds):
  - Disables liveness probe until startupProbe succeeds
  - failureThreshold: high (e.g., 30) × periodSeconds: 10s = 300s max startup time
  - After startupProbe succeeds: liveness and readiness take over

Anti-patterns:
  ❌ Liveness calls external DB → DB outage causes restart loop → cascading failure
  ❌ No startup probe + high initialDelaySeconds → slow starts killed as unhealthy
  ❌ Readiness always returns 200 → broken pods receive traffic → errors served to users
  ❌ Same endpoint for liveness and readiness → coupled semantics; cannot independently fail
```

### Resource Configuration Matrix

| Concern | Setting | Recommendation |
| --- | --- | --- |
| Scheduler placement | CPU request, memory request | Set to P95 steady-state observed usage; use VPA recommendations |
| CPU throttling | CPU limit | Omit for latency-sensitive; set 2-4x request for batch workloads |
| OOMKill prevention | Memory limit | Set equal to memory request (guaranteed QoS); add headroom for GC |
| Autoscaling trigger | HPA targetAverageUtilization | 50-70% CPU; requests must be set or HPA cannot function |
| Event-driven scaling | KEDA ScaledObject | Kafka: lagTarget; SQS: queueLength; Cron: schedule |
| Spot node protection | PodDisruptionBudget | `minAvailable: 1` or `maxUnavailable: 25%` |
| Topology | topologySpreadConstraints | Spread across zones: `whenUnsatisfiable: DoNotSchedule` |

### Rollout Strategy Selection

| Strategy | Mechanism | Zero-downtime | Rollback speed | Use when |
| --- | --- | --- | --- | --- |
| RollingUpdate (default) | Incremental pod replacement | Yes (if readiness correct) | `kubectl rollout undo` (fast) | Standard stateless services |
| Recreate | Kill all, then create new | No (downtime) | Redeploy old version | Dev/test; single-instance batch; stateful with schema lock |
| Canary (Argo Rollouts) | Route % traffic to new version | Yes | Automated on metric threshold | Production; high-traffic; risk-averse releases |
| Blue-Green | Full parallel environment | Yes (instant cutover) | Switch traffic back instantly | Regulated; financial; zero-tolerance error rate |

# Selection Rules

Select this capability when **Kubernetes workload design, routing, health, scaling, or security posture** is the primary concern. Adjacent routing:

- Prefer `containerization` when the primary concern is container image hardening, build, and registry.
- Prefer `ci-cd` when the primary concern is deployment pipeline automation, environment promotion, and release triggers.
- Prefer `observability` when the primary concern is distributed tracing, metrics collection, and alerting.
- Prefer `release-rollback` when the primary concern is coordinating rollback across code, config, schema, and service integrations.

# Risk Escalation Rules

Escalate when: the workload is public-facing (Ingress/Gateway exposes it to the internet without an auth layer); the workload runs as root or with privileged SecurityContext; the workload accesses another tenant's namespace resources; the ServiceAccount has cluster-level RBAC bindings; a StatefulSet modification changes PersistentVolume claims; NetworkPolicy is absent and the namespace contains sensitive workloads; or a database migration is coupled to the rollout and cannot be rolled back independently.

# Critical Details

- **Liveness calling a database.** A liveness probe calls `GET /health` which checks DB connectivity. The database goes down during maintenance. All pods fail the liveness check. All pods restart. The restart-storm causes the DB connection pool to be re-established under load. Recovery takes 10x longer than if liveness had not called the DB. Fix: liveness checks only process health; readiness checks dependencies.
- **Memory limit = memory request.** If memory request < memory limit, the pod has Burstable QoS. Under node memory pressure, Kubernetes will evict Burstable pods first. A Java service with 512Mi request and 1Gi limit bursts to 800Mi; node is under pressure; pod evicted; service unavailable. Fix: set memory limit = request for Guaranteed QoS on critical services.
- **Secret in ConfigMap.** ConfigMaps are not encrypted at rest in etcd by default. A database password stored in a ConfigMap (not a Secret) is visible to anyone with `kubectl get configmap` RBAC. Even Kubernetes Secrets are only base64-encoded unless etcd encryption at rest is enabled. Use ExternalSecrets or Sealed Secrets for all credential values.
- **No PodDisruptionBudget during node drain.** A cluster upgrade drains nodes. Without a PDB, all replicas of a Deployment may be evicted simultaneously. For a 2-replica deployment: both pods evicted → service unavailable during drain. PDB `minAvailable: 1` prevents this.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Liveness probe checks DB connectivity | DB maintenance → liveness fails → pods restart → restart storm → extended outage |
| Secret in ConfigMap or manifest YAML | Credential visible to anyone with namespace read access; base64 is not encryption |
| No resource requests | Scheduler blind to pod needs; noisy neighbors steal CPU/memory; workload starved |
| Memory limit >> memory request | Burstable QoS; evicted first under pressure; unexpected pod loss |
| Default ServiceAccount with broad RBAC | Any compromised pod has cluster permissions; lateral movement risk |
| No NetworkPolicy | Any pod reaches any other pod; compromised pod can exfiltrate from adjacent services |
| No PodDisruptionBudget | Node drain evicts all replicas simultaneously; zero-downtime promise broken |
| Rollback = kubectl rollout undo only | Reverts image; does not revert ConfigMap, schema migration, Ingress rule; service broken |

# Failure Modes

- Liveness probe calls DB; DB maintenance window; all pods restart; 10-minute outage during planned maintenance.
- Database password in ConfigMap; read by developer with `kubectl get configmap -n prod`; credential leaked.
- No resource requests; noisy batch job starves API pod of CPU; latency spikes; alert fires during business hours.
- Memory request 256Mi, limit 1Gi; node under pressure; pod evicted at 600Mi; service unavailable; no readiness signal given.
- Default ServiceAccount; compromised pod reads Secrets from other namespaces via cluster RBAC; lateral movement.
- No NetworkPolicy; compromised frontend pod makes internal calls to payment service directly; bypasses API gateway.
- Node drain during upgrade; 2-replica deployment; both pods evicted simultaneously (no PDB); 60-second outage.
- Canary rollout with no automated rollback; error rate 10%; alert fires but no automated rollback; on-call manually reverts after 20 minutes.

# Output Contract

Return a Kubernetes workload design with:

- `maturity_rationale` (why Kubernetes is justified; operational ownership confirmed)
- `workload_type` (Deployment / StatefulSet / Job / CronJob / DaemonSet; rationale)
- `image` (registry, tag policy: semver tag not `latest`; image pull policy)
- `config_secrets` (ConfigMap keys; Secret source: ExternalSecrets / Sealed Secrets; mount method)
- `service_account` (dedicated SA name; RBAC bindings; Workload Identity annotation if cloud API access needed)
- `security_context` (pod + container: runAsNonRoot, allowPrivilegeEscalation, readOnlyRootFilesystem, seccompProfile)
- `resources` (CPU request/limit; memory request/limit; QoS class target)
- `probes` (liveness: endpoint, what it checks, thresholds; readiness: endpoint, dependencies checked; startup if needed)
- `service` (ClusterIP / LoadBalancer / NodePort; port mapping; session affinity)
- `routing` (Ingress / Gateway API: host, path, TLS, timeout, auth annotation, rate limit)
- `network_policy` (ingress allow rules; egress allow rules; default-deny namespace policy)
- `scaling` (HPA: metric, target utilization; KEDA: trigger type; PodDisruptionBudget: minAvailable)
- `topology` (topologySpreadConstraints: zone spread; node affinity/anti-affinity)
- `rollout_strategy` (RollingUpdate / Canary / Blue-Green; rollback trigger; rollback procedure for config + schema)
- `observability` (metrics endpoints; log format: structured JSON; distributed trace context propagation)
- `verification` (post-deploy health check command; smoke test; rollback decision criteria)

# Quality Gate

The Kubernetes workload design is complete only when:

1. Liveness, readiness, and startup probes designed with correct semantics (liveness does not call external deps).
2. Resource requests set on every container; memory request = memory limit for critical workloads.
3. Secrets sourced from ExternalSecrets/Sealed Secrets — not ConfigMaps, manifests, or env literals.
4. SecurityContext: `runAsNonRoot: true`, `allowPrivilegeEscalation: false`, `readOnlyRootFilesystem: true`.
5. Dedicated ServiceAccount per workload with minimum RBAC.
6. NetworkPolicy: namespace default-deny in place; explicit allow rules added.
7. PodDisruptionBudget defined for all HA workloads.
8. Rollout strategy selected; rollback procedure documented (image + config + schema scope).
9. Gateway/Ingress: TLS configured; auth enforced; timeout set; rate limit configured.
10. Operational ownership confirmed: team owns on-call, deployment pipeline, and incident runbook.

# Used By

- delivery-release-gate
- reliability-observability-gate

# Handoff

Hand off to `containerization` for image hardening and registry; `ci-cd` for deployment pipeline and environment promotion; `observability` for metrics, traces, and alerting; `release-rollback` for cross-surface rollback coordination.

# Completion Criteria

The capability is complete when **the workload can be scheduled with correct resources, routed safely, observed, scaled automatically, and rolled back with an explicit procedure covering image, configuration, and schema scope** — secured by non-root execution, minimal RBAC, secret injection, and network policy.
