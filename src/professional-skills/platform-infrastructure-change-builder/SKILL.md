---
name: platform-infrastructure-change-builder
description: "`task-agent` infrastructure source changes within authority, excluding production mutation and review."
---

# platform-infrastructure-change-builder

## Role

Begin by inspecting target/state/recovery. As `task-agent`, change source, run minimal validation, and do not proceed to production mutation.

## When To Use

- infrastructure implementation
- Terraform OpenTofu CloudFormation Pulumi Helm Kustomize controller or operator source change
- cloud IAM network managed service service mesh API gateway CI runner observability secret or environment definition change

## Do Not Use

- frontend installed-client or backend product behavior
- documentation-only change or multi-task planning
- production apply deployment release or rollback approval
- independent review

## Required Inputs

- accepted design and expected desired-state change
- exact account project subscription region cluster and environment target
- current state backend lock or writer model and drift assumptions
- provider module chart controller and tool versions
- authority boundary recovery owner and non-production validation path

## Professional Decision Rules

- Bind target, owner, state/backend/lock/writer, and versions.
- Select the smallest recoverable change from current identity/drift evidence.
- Compare proposal unknowns and destructive/privilege/network/secret/cost/dependency effects.

## High-Value Gotchas

- A source diff, render, plan, preview, or change set is neither mutation authority nor convergence proof.
- Provider defaults and live control-plane behavior can differ from source and recorded state.
- Concurrent writers, stale locks, imports, moves, and drift can invalidate a locally correct proposal.

## Execution Checklist

1. Inspect owner, target, state/backend/writer model, versions, dependencies, and recovery.
2. Map replacement, destruction, privilege, network, secret, cost, drift, and dependency effects.
3. Choose the smallest source change that preserves state identity and recovery.
4. Validate rendered artifacts and fresh non-mutating proposal evidence against the exact target and versions.
5. Record unknowns, unverified production state, recovery owner, residual risk, and release boundary.
6. Route production apply, deployment, release, and rollback authority to `delivery-release-gate`.

## Stop / Escalation Conditions

- Stop while authority, state/writer/recovery, or effects remain unresolved.

## Output Contract

- owner/source, target/version, proposal/effects/recovery, proof limits, release boundary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [iac source contracts](references/iac-source-contracts.md) | targeted | Terraform OpenTofu Pulumi or CloudFormation state identity plan preview or change-set semantics affect the change | Only Kubernetes-native rendering or controller behavior is affected | task-agent | proof-limit, selected-approach, validation-plan |
| [kubernetes source contracts](references/kubernetes-source-contracts.md) | targeted | Kubernetes objects controllers operators Helm Kustomize field ownership hooks CRDs or final rendering affects the change | The change uses no Kubernetes API or packaging surface | task-agent | proof-limit, selected-approach, validation-plan |
