---
name: platform-infrastructure-change-builder
description: "`task-agent` infrastructure source changes within authority, excluding production mutation and review."
---

# platform-infrastructure-change-builder

## Role

As `task-agent`, distinguish reusable source/render work from a change bound to a deployment target. Inspect the applicable source, versions, consumers, and existing state/recovery mechanisms; change source and run minimal validation without production mutation.

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
- for a target-bound change: applicable account/project/subscription/region/cluster/environment and current state/backend/lock/writer/drift evidence
- for reusable modules, templates, or render tests: declared interfaces, versions, consumers, and representative render/test inputs; no invented live target
- provider module chart controller and tool versions
- authority boundary and non-production validation path; recovery owner when the affected mechanism has deployed state or recovery behavior

## Professional Decision Rules

- Bind source owner, versions, and affected consumers; require target/state/backend/lock/writer evidence only where the current change depends on those mechanisms.
- Preserve existing identity and recovery from current evidence; reusable render work need not acquire a production target or state backend.
- Compare proposal unknowns and destructive/privilege/network/secret/cost/dependency effects.

## High-Value Gotchas

- A source diff, render, plan, preview, or change set is neither mutation authority nor convergence proof.
- Provider defaults and live control-plane behavior can differ from source and recorded state.
- Concurrent writers, stale locks, imports, moves, and drift can invalidate a locally correct proposal.

## Execution Checklist

1. Inspect owner, versions, dependencies, and whether this is reusable source or target-bound work.
2. Map replacement, destruction, privilege, network, secret, cost, drift, and dependency effects.
3. Choose the smallest source change that preserves state identity and recovery.
4. Validate reusable source with representative render/tests; bind target-specific non-mutating proposals to the actual target, applicable state, and versions.
5. Record applicable unknowns, proof limits, recovery responsibility, residual risk, and release boundary.
6. Keep production apply, deployment, release, and rollback approval outside this Skill's authority.

## Stop / Escalation Conditions

- Stop while authority, applicable state/writer/recovery, or material effects remain unresolved; absent production targets do not block reusable source/render work.

## Output Contract

- owner/source, target/version, proposal/effects/recovery, proof limits, release boundary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [iac source contracts](references/iac-source-contracts.md) | targeted | Terraform OpenTofu Pulumi or CloudFormation state identity plan preview or change-set semantics affect the change | Only Kubernetes-native rendering or controller behavior is affected | task-agent | proof-limit, selected-approach, validation-plan |
| [kubernetes source contracts](references/kubernetes-source-contracts.md) | targeted | Kubernetes objects controllers operators Helm Kustomize field ownership hooks CRDs or final rendering affects the change | The change uses no Kubernetes API or packaging surface | task-agent | proof-limit, selected-approach, validation-plan |
