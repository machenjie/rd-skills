---
name: kubernetes-gateway
description: Defines Kubernetes workload, service, ingress or gateway, probes, resources, rollout, and rollback only when operational maturity justifies Kubernetes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "74"
changeforge_version: 0.1.0
---

# Mission

Deploy and operate Kubernetes workloads deliberately: choose Kubernetes only when the platform maturity justifies it, then define workload shape, routing contract, health semantics, resource budgets, security posture, rollout strategy, rollback scope, and validation evidence before the change is accepted.

# When To Use

Use this capability when a change creates or modifies Kubernetes workloads, Services, Ingress, Gateway API, DNS/CDN/WAF/load balancer exposure, probes, resources, HPA/KEDA/VPA, PodDisruptionBudget, ServiceAccount, RBAC, NetworkPolicy, ConfigMaps, Secrets, cloud identity bindings, Helm charts, GitOps manifests, CRDs, hooks, or rollout/rollback behavior.

# Do Not Use When

Do not use this capability to justify Kubernetes for a workload with no platform owner, deployment pipeline, rollback path, centralized logs/metrics, secret-management process, or network policy enforcement. Do not use it for image construction alone; route image build and base-image hardening to `containerization`. Do not treat Kubernetes as simpler than a managed runtime when the team cannot operate the cluster surface.

# Stage Fit

Use during architecture/design for runtime selection, coding and refactoring when manifests or charts change, code-review when gateway/security/rollout posture changes, testing when rendered manifests or policy checks are needed, release when Helm/GitOps/deploy commands are involved, and handoff when residual operational risk must be explicit.

# Non-Negotiable Rules

- Readiness controls traffic, liveness restarts only stuck processes, and startup protects slow init. Do not use one endpoint with identical semantics for all three.
- Every container has CPU and memory requests; critical services justify memory request/limit shape and HPA/KEDA inputs from observed or forecast load.
- Secrets never appear in manifests, `values.yaml`, ConfigMaps, container args, or literal environment values; use approved secret sources and redaction.
- Pod and container security context uses non-root execution, no privilege escalation, read-only root filesystem where feasible, and seccomp/AppArmor where supported.
- ServiceAccount, RBAC, cloud identity, and NetworkPolicy are workload-specific and least-privilege; default broad access is a blocker.
- Gateway/Ingress/LoadBalancer/DNS/CDN/WAF changes state public exposure, tenant/namespace blast radius, TLS/auth policy, timeout/rate-limit policy, owner, and rollback.
- Rollback covers image, ConfigMap, Secret version, route, feature flag, schema, CRD, hook, and external config scope; `kubectl rollout undo` is not enough.
- Helm/GitOps changes render deterministically before deployment and include schema validation, lint/template output, diff, policy checks, CRD/hook handling, and rollback limits.

# Industry Benchmarks

Anchor against CIS Kubernetes Benchmark, NSA/CISA Kubernetes Hardening Guide, Kubernetes Pod Security Standards, Gateway API, HPA/KEDA/VPA, PodDisruptionBudget, Argo Rollouts/Flagger, Helm release controls, ExternalSecrets/CSI Secret Store/Vault patterns, Prometheus/kube-state-metrics, and GitOps rendered-diff discipline. Keep deep checklists in [references/checklist.md](references/checklist.md) and keep this body focused on routing, gates, and closure evidence.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities / gates | Skip guidance |
| --- | --- | --- | --- | --- | --- |
| Runtime fit | New service, migration from PaaS/VM, platform ownership unclear. | Decide whether Kubernetes is justified. | Owner, on-call/runbook, deploy pipeline, rollback path, observability, secret and network policy readiness. | `delivery-release-gate`, `reliability-observability-gate` | Skip Kubernetes recommendation when a simpler managed runtime meets scale/reliability needs. |
| Workload contract | Deployment/StatefulSet/DaemonSet/Job/CronJob or pod spec changes. | Match workload type, lifecycle, storage, shutdown, scheduling, and topology to behavior. | Workload rationale, replicas, termination grace, volume/PVC impact, topology and PDB decision. | `containerization`, `release-rollback` | Skip stateful recommendations for stateless workloads with no persistent data. |
| Traffic exposure | Service, Ingress, Gateway API, DNS, CDN, WAF, LoadBalancer, auth, timeout, or route change. | Control exposure, tenant blast radius, TLS/auth, routing, and rollback. | Rendered route diff, host/path/TLS/auth/timeouts/rate limits, exposure owner, rollback step. | `security-privacy-gate`, `delivery-release-gate` | Skip public-exposure analysis only for internal-only services with confirmed namespace/network boundaries. |
| Health/resources/scaling | Probe, requests/limits, HPA/KEDA/VPA, PDB, or topology spread changes. | Prevent traffic to unready pods, restart storms, starvation, and rollout capacity loss. | Probe semantics, resource baseline, scaling metric, PDB, saturation alert, post-deploy check. | `reliability-observability-gate`, `observability`, `performance-budgeting` | Skip autoscaling design for one-shot Jobs unless concurrency or retry pressure is material. |
| Security/policy/secrets | ServiceAccount, RBAC, NetworkPolicy, cloud identity, Secret, ConfigMap, or values change. | Enforce least privilege, secret-safe config, and namespace isolation. | RBAC diff, network allowlist, secret source, identity binding, policy check result. | `security-privacy-gate`, `secret-configuration-security` | Skip cluster-wide RBAC only when workload uses no API/cloud identity and namespace policy is unchanged. |
| Helm/GitOps release | Chart, values, schema, CRD, hook, rendered manifest, upgrade, rollback, or controller sync change. | Make deployment deterministic and reversible enough for release. | `helm lint/template`, schema, diff, policy result, CRD/hook order, atomic/waited or GitOps sync evidence. | `ci-cd`, `release-rollback`, `agent-tool-permission-sandbox` | Skip live command guidance when the task is design-only and no release action will run. |

# Selection Rules

Select this capability when Kubernetes workload design, routing, health, scaling, gateway exposure, Helm/GitOps release, or cluster security posture is primary. Adjacent routing:
- Prefer `containerization` when the primary concern is container image hardening, build, and registry.
- Prefer `ci-cd` when the primary concern is deployment pipeline automation, environment promotion, and release triggers.
- Prefer `observability` when the primary concern is metric, log, trace, dashboard, and alert design.
- Prefer `release-rollback` when the primary concern is coordinating rollback across code, config, schema, and service integrations.
- Add `agent-tool-permission-sandbox` before any Kubernetes, Helm, GitOps, cloud, secret, DNS, WAF, or rollback command that can mutate shared or production state.

# Technical Selection Criteria

Evaluate workload type, operational ownership, environment scope, namespace and tenant boundary, traffic exposure, health semantics, requests/limits, autoscaling metric, PDB/topology, RBAC/identity, NetworkPolicy, secret source, ConfigMap behavior, Helm/GitOps packaging, CRD/hook semantics, rollback breadth, observability, validation commands, source-vs-generated boundary, and release owner. A usable answer is either approved with evidence, blocked with the missing evidence, or scoped as design-only with no live mutation.

# Proactive Professional Triggers

- **Signal:** Ingress, Gateway API, LoadBalancer, DNS, CDN, WAF, namespace routing, or cloud identity expands reach. **Hidden risk:** a route or identity change creates public exposure, tenant leakage, or privilege escalation. **Required professional action:** require rendered route/policy review, exposure owner, rollback path, and auth/TLS/WAF decision. **Route to:** `security-privacy-gate`, `delivery-release-gate`, `kubernetes-gateway`. **Evidence required:** rendered manifest or diff, host/path/TLS/auth policy, blast-radius statement, rollback step.
- **Signal:** `kubectl`, Helm, GitOps sync, cloud, secret, DNS, WAF, or rollback command may write shared state without permission/sandbox classification. **Hidden risk:** an agent mutates live infrastructure outside the reviewed boundary. **Required professional action:** classify action class, permission state, sandbox, dry-run/rendered diff, rollback/revert path, and redaction rule before execution. **Route to:** `agent-tool-permission-sandbox`, `delivery-release-gate`. **Evidence required:** command, scope, dry-run or rendered output, approval boundary, rollback note.
- **Signal:** Probes, requests/limits, autoscaling, PDB, topology spread, or rollout strategy are missing or copied from another service. **Hidden risk:** rollouts send traffic to unready pods, trigger restart storms, or lose all replicas during node drain. **Required professional action:** design service-specific health and capacity controls and tie them to release watch metrics. **Route to:** `reliability-observability-gate`, `observability`, `performance-budgeting`. **Evidence required:** probe semantics, resource baseline, HPA/KEDA metric, PDB/topology decision, alert/query.
- **Signal:** ServiceAccount, RBAC, NetworkPolicy, Secret source, ConfigMap, or workload identity broadens access. **Hidden risk:** compromised pods gain lateral movement, secret read access, or cloud permissions. **Required professional action:** apply least privilege, default-deny networking, secret-safe sourcing, and policy-as-code checks. **Route to:** `security-privacy-gate`, `secret-configuration-security`. **Evidence required:** RBAC diff, network allowlist, secret source, identity binding, policy result.
- **Signal:** Helm chart, values, CRD, hook, or GitOps manifest changes without lint/template/schema/diff/policy and rollback-scope evidence. **Hidden risk:** the release applies an unreviewed manifest, unsafe default, irreversible CRD change, or stuck hook job. **Required professional action:** require deterministic render validation, CRD/hook order, atomic/waited or controller sync behavior, and rollback limits. **Route to:** `ci-cd`, `release-rollback`, `delivery-release-gate`. **Evidence required:** command output, exit code, rendered artifact/report, CRD/hook note, rollback scope.

# Risk Escalation Rules

Escalate when a workload is public-facing, exposure expands, privileged or root execution is proposed, cluster-level RBAC or broad cloud identity appears, NetworkPolicy is absent around sensitive workloads, StatefulSet/PVC behavior changes, CRD schema rollback is unclear, a database migration is coupled to deployment, or release commands can mutate shared state without a reviewed permission boundary.

# Critical Details

- Liveness may check process responsiveness; readiness may check dependencies; startup absorbs initialization. Mixing them turns a dependency outage into a restart storm.
- Memory request/limit shape affects QoS and eviction behavior; copying values from another workload hides real capacity risk.
- ConfigMaps are not a credential container, and committed Kubernetes Secrets are not a safe secret-management process.
- PDB and topology spread are part of the availability contract, not optional decoration, for multi-replica services.
- Helm rollback does not safely undo CRDs, data migrations, external routes, secret versions, or provider-side configuration.

# Failure Modes

- **Restart storm:** liveness calls the database; maintenance makes every pod restart; recovery is slower than dependency restoration.
- **Credential leak:** password appears in ConfigMap, values file, or committed Secret YAML; namespace readers can retrieve it.
- **Scheduler blindness:** no resource requests; a noisy neighbor starves the API and latency spikes without clear capacity evidence.
- **Eviction surprise:** memory request is far below limit; node pressure evicts a critical pod before readiness protects traffic.
- **Privilege spread:** default ServiceAccount or cluster role lets a compromised pod read unrelated Secrets or APIs.
- **Network bypass:** absent NetworkPolicy lets one namespace call an internal service directly and bypass gateway controls.
- **Availability gap:** node drain evicts all replicas because PDB/topology spread was not defined.
- **Rollback illusion:** `kubectl rollout undo` restores the image while the Gateway rule, Secret version, or schema remains incompatible.
- **Helm hook stall:** non-idempotent hook job hangs during upgrade; release is stuck and rollback semantics are unclear.

# Reference Loading Policy

The `SKILL.md` body carries routing, gates, and closure rules. Load [references/checklist.md](references/checklist.md) when drafting a concrete manifest/chart review, production/shared-environment Kubernetes plan, Gateway/Ingress exposure review, RBAC/NetworkPolicy/secret review, Helm/GitOps release plan, CRD/hook decision, or rollout/rollback checklist. Do not load it for a local-only design note with no cluster, release, route, or secret surface.

# Output Contract

Return a `kubernetes_gateway_plan` with:
- `mode_selected` and trigger signal.
- `boundaries_inspected`: workload, namespace, route, cloud exposure, identity/RBAC, network policy, config/secret, Helm/GitOps, rollout, observability, and skipped boundaries with reason.
- `workload_contract`: type, lifecycle, replicas, shutdown, storage/PVC, topology, PDB, and image tag policy.
- `health_resources_scaling`: probes, requests/limits, HPA/KEDA/VPA, saturation signal, and post-deploy watch metric.
- `traffic_security`: Service, Ingress/Gateway, DNS/CDN/WAF/load balancer, TLS/auth/timeouts/rate limits, ServiceAccount/RBAC, NetworkPolicy, secret source, and security context.
- `release_validation`: command, validator/test, output, exit code, rendered artifact/report, diff, policy result, and freshness status.
- `rollback_plan`: image, config, secret, route, schema, CRD, hook, and external dependency rollback or forward-fix scope.
- `residual_risk` and next gate or handoff owner.

# Evidence Contract

Close Kubernetes work only when these answers are concrete:
- **Boundaries inspected:** source manifests/charts, namespace, route, exposure, identity/RBAC, NetworkPolicy, secrets/config, release path, observability, rollback, and skipped scope.
- **Validation evidence:** exact command, validator or test, output summary, exit code, artifact/report path, rendered diff/policy result, and freshness relative to the final edit.
- **What evidence proves:** scheduling contract, route intent, secret-safe config, policy posture, rendered manifest validity, rollout readiness, or rollback command readiness.
- **What evidence does not prove:** live cluster admission, provider-side DNS/CDN/WAF behavior, production capacity, future secret rotation, actual canary success, or data/schema reversibility unless verified separately.
- **Reuse / placement rationale:** why the responsibility belongs in Kubernetes manifests, Helm chart, GitOps overlay, platform policy, CI gate, or adjacent capability.
- **Residual risk:** unverified cluster/provider behavior, missing test edge, irreversible CRD/schema/provider state, manual rollback step, or operational ownership gap.
- **Next gate:** `delivery-release-gate`, `reliability-observability-gate`, `security-privacy-gate`, `quality-test-gate`, or `agent-tool-permission-sandbox` as applicable.

# Benchmark Coverage

This capability covers Kubernetes workload fit, Gateway/Ingress exposure, pod security, least-privilege identity, NetworkPolicy, secret sourcing, probes, resource and scaling controls, PDB/topology availability, Helm/GitOps deterministic rendering, CRD/hook risk, rollout and rollback scope, observability handoff, and tool-permission boundaries for cluster-mutating actions.

# Routing Coverage

Routes from `change-forge-router`, `delivery-release-gate`, `reliability-observability-gate`, `security-privacy-gate`, `ci-cd`, `containerization`, `secret-configuration-security`, and `release-rollback` should arrive here when Kubernetes manifests, charts, routes, probes, resources, security posture, or rollout behavior need design or review. Route away when the primary need is only image construction, pipeline mechanics, secret rotation design, observability instrumentation, or cross-surface rollback orchestration.

# Quality Gate

1. Liveness, readiness, and startup probes designed with correct semantics (liveness does not call external deps).
2. Resource requests are set on every container and scaling metrics have a defensible baseline or forecast.
3. Secrets are sourced from approved secret mechanisms, not ConfigMaps, manifests, `values.yaml`, or env literals.
4. SecurityContext covers non-root execution, privilege escalation, writable filesystem need, and seccomp/AppArmor where supported.
5. Dedicated ServiceAccount per workload with minimum RBAC.
6. NetworkPolicy default-deny and explicit allow rules are reviewed for sensitive namespaces.
7. PDB and topology spread are defined or explicitly skipped with reason.
8. Gateway/Ingress/LoadBalancer exposure has TLS, auth, timeout, rate limit, blast-radius, owner, and rollback decision.
9. Rollout and rollback cover image, config, secret, route, schema, CRD, hook, and external config scope.
10. Operational ownership confirmed: team owns on-call, deployment pipeline, and incident runbook.
11. Helm/GitOps changes pass lint/template/schema/diff/rendered-manifest/policy checks or are disclosed as not verified.
12. CRDs and hooks have ordering, idempotency, timeout, service account, and rollback limitations documented.
13. Tool permission, sandbox boundary, dry-run/rendered diff, rollback path, and redaction rule are recorded before live cluster or cloud mutation.

# Used By

- delivery-release-gate
- reliability-observability-gate

# Handoff

Hand off to `containerization` for image hardening and registry, `ci-cd` for deployment pipeline and environment promotion, `observability` for metrics/traces/alerts, `security-privacy-gate` for exposure/RBAC/secret risk, `release-rollback` for cross-surface recovery, and `agent-tool-permission-sandbox` before live Kubernetes/Helm/cloud mutations.

# Completion Criteria

The capability is complete when the workload is justified, schedulable, routable, least-privileged, secret-safe, observable, scalable, validated by current rendered or policy evidence, and recoverable through an explicit rollback/forward-fix plan that covers Kubernetes, Helm/GitOps, gateway, config, secret, schema, CRD, hook, and external surfaces within the stated evidence limits.
