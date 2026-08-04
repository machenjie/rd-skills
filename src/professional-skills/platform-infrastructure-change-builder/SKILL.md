---
name: platform-infrastructure-change-builder
description: "Use `task-agent` for accepted infrastructure-as-code, cluster, cloud, delivery-platform, or environment-definition source changes. Skip production apply/deploy, release approval, and independent review."
---

# platform-infrastructure-change-builder

## Role

Support `task-agent` in changing declarative platform and infrastructure source
without authorizing or performing production mutation.

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
- exact account, project, subscription, region, cluster, and environment target
- current state backend, lock or writer model, and drift assumptions
- provider, module, chart, controller, and tool versions
- authority boundary, recovery owner, and non-production validation path

## Professional Decision Rules

- Keep source configuration, recorded state, provider actual state, and effective deployed state distinct.
- Change the smallest owning source after inspecting modules, overlays, generators, consumers, and reuse.
- Pin decisions to the repository's tool, provider, plugin, module, chart, and API versions.
- Treat render, validation, plan, preview, and change set as scoped evidence rather than execution approval.
- Inspect unknown, drift, replace, destroy, privilege, network, secret, cost, and dependency effects when reachable.
- Keep secret values out of source, plans, renders, logs, diffs, and handoff evidence.

## High-Value Gotchas

- A clean preview does not prove authorization, quota, capacity, convergence, or application health.
- A stale plan can differ from the next apply after source, state, provider, or target changes.
- Partial infrastructure mutation is not a transaction and may require forward reconciliation.
- Validating a base file does not prove the final overlay, generated manifest, chart, or stack.
- Target, exclude, prune, force, replace, and ignore controls can hide or transfer ownership.

## Execution Checklist

1. Inspect the accepted design, owning source, minimum consumer, state contract, target identity, versions, tests, and generated surface.
2. Map the reachable outcome set: normal, invalid, unknown, drifted, destructive, privilege-changing, secret-bearing, recovery.
3. Implement the smallest bounded source change without applying or deploying it to production.
4. Run applicable format, lint, static validation, render, schema, policy, and non-production tests.
5. Produce a fresh non-mutating plan, preview, change set, or diff when the tool and authority allow it.
6. Inspect whether proposed effects have decision-usable evidence.
7. Stop closure when that evidence is not decision-usable.

## Stop / Escalation Conditions

- Stop when target account, project, subscription, region, cluster, environment, authority, state backend, or writer lock is unclear.
- Stop on an unapproved replace, destroy, prune, force, import, state rewrite, privilege escalation, network exposure, or secret disclosure.
- Stop before any production apply, deploy, rollout, migration, or irreversible mutation.
- Route release, rollback, go/no-go, production recovery, and containment decisions to `delivery-release-gate`.
- Stop when a final preview is unavailable or no longer matches the final source, state, versions, and target.
- Do not perform or claim independent review.

## Output Contract

- changed files with source owner, reuse, target, and version decisions
- rendered or validated artifacts and current command evidence
- fresh plan, preview, change-set, or diff evidence with unknown and freshness limits
- replace, destroy, privilege, network, secret, cost, drift, and dependency findings
- unverified production state, recovery owner, residual risk, and release boundary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [iac source contracts](references/iac-source-contracts.md) | targeted | Terraform OpenTofu Pulumi or CloudFormation state identity plan preview or change-set semantics affect the change | Only Kubernetes-native rendering or controller behavior is affected | task-agent | proof-limit, selected-approach, validation-plan |
| [kubernetes source contracts](references/kubernetes-source-contracts.md) | targeted | Kubernetes objects controllers operators Helm Kustomize field ownership hooks CRDs or final rendering affects the change | The change uses no Kubernetes API or packaging surface | task-agent | proof-limit, selected-approach, validation-plan |
