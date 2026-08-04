---
name: kubernetes-gateway
description: "`task-agent`/`review-agent`: use when a Kubernetes workload, route, identity, health, capacity, or rollout boundary changes; skip image-only, pipeline-only, and non-cluster work."
---

# kubernetes-gateway

## Registry Trigger

**Use when**

- change Kubernetes workload lifecycle routing identity health capacity scheduling exposure or cluster rollout behavior

**Do not use when**

- work is limited to image construction hosted pipeline mechanics data migration or a runtime outside the Kubernetes cluster boundary

## Skill Role

Define Kubernetes desired and effective runtime boundaries for workload lifecycle, identity, traffic, capacity, rollout, and recovery. Exclude image construction, pipeline mechanics, and data migration.

## High-Value Rules

- Choose workload and controller semantics from identity, restart, storage, scheduling, concurrency, completion, and ownership needs. A familiar resource kind is not evidence that its lifecycle matches the process.
- Separate startup, readiness, liveness, termination, and traffic-drain outcomes. Probe the failure a restart or traffic decision can actually correct; dependency failure in liveness can create a restart storm.
- Derive requests, limits, scaling, disruption, placement, failure-domain behavior, and proof limits from current workload consequences.
- Bind service identity, workload identity, namespace, permissions, secret or configuration source, and network reachability to the changed trust boundary. Isolation choices come from current platform policy and reachable access rather than a universal manifest recipe.
- Define the traffic contract across service and gateway layers: listener, host/path/method, backend, TLS, authentication, timeout, retry, body, rate, source, tenant exposure, and external DNS/edge ownership that actually change.
- Define one release identity across rendered workload, image digest, configuration and secret versions, routes, policies, and target.
- Verify intended manifests separately from admitted and live state.
- Model mixed-version behavior, in-flight work, hooks, custom resources, persistent state, external routes, watch signals, stop conditions, and reversal or forward recovery. Live mutation requires explicit target and authority.

## Anti-Patterns

- Copying probes, resources, replica/disruption settings, identities, or network policy from another workload without consequence evidence.
- Treating a rendered manifest, package rollback, or controller success as proof of live traffic, capacity, secret rotation, data, or external-route recovery.
- Folding image provenance, pipeline enforcement, data migration, and final release approval into the cluster resource decision.
- Expanding public, tenant, namespace, or cloud-identity exposure without an explicit owner and reversal boundary.

## Stop Conditions

- Escalate when live target/authority, privilege, public exposure, stateful lifecycle, custom-resource compatibility, traffic ownership, or a coupled irreversible effect cannot be bounded before mutation.

## Output Contract

- Return a Kubernetes runtime decision: define workload, route, identity, health, capacity, scheduling, rollout, effective-state proof, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Workload lifecycle health capacity identity traffic or rollout mechanisms remain open | Current cluster policy controller behavior and workload consequence select one bounded design | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A cluster change crosses workload state health capacity identity traffic exposure or recovery boundaries | No Kubernetes desired or effective runtime boundary changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Rendered intent workload identity traffic capacity rollout or live-authority claims need fresh proof | No cluster-runtime or effective-state claim awaits validation | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
