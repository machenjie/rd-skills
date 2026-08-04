---
name: infrastructure-as-code-safety
description: "`analysis-agent`/`task-agent`/`review-agent`: use for infrastructure state, identity, drift, replacement, destruction, or recovery; skip docs, live apply, and provider-only policy."
---

# infrastructure-as-code-safety

## Registry Trigger

**Use when**

- change desired-state infrastructure source where state, identity, drift, destruction, or recovery can alter the outcome
- interpret a plan, preview, change set, render, or diff with freshness or unknown-effect limits

**Do not use when**

- work is documentation-only or simple configuration text without a desired-state source change
- work requests production apply, deployment, release or rollback approval, or irreversible mutation
- work concerns provider quota or platform policy without infrastructure-as-code source

## Skill Role

Define cross-tool IaC safety for state, proposal, identity, graph, external effects, and recovery. Exclude Builder workflow, provider policy, secret lifecycle, data migration, and production authority.

- Keep Kubernetes desired and recorded IaC state, source identity, plan, and external-effect decisions here.
- Route workload lifecycle, health, capacity, traffic, scheduling, runtime reconciliation, and runtime recovery to `kubernetes-gateway`.

## High-Value Rules

- Reconcile material disagreements only after separating desired, recorded, provider-observed, and effective state.
- Bind target, remote state backend, workspace or stack, writer, and locking semantics before trusting a proposal.
- Bind proposal evidence to current source, state, target, dependency, provider version, tool version, unknowns, omissions, staleness, and apply-gap limits.
- Treat targeted apply, exclude, prune, and force as incomplete graph evidence requiring dependency and reconciliation inspection.
- Classify import, move, rename, adoption, replacement, and removal by source-to-remote identity and update, replace, destroy, orphan, or external-owner outcomes.
- Inspect privilege, network exposure, deletion protection, secret-bearing output, and irreversibility before accepting source.
- Select source reversion, state recovery, remote restoration, or forward reconciliation for every surface that can remain changed.
- Keep plan, state encryption, protection, drift, and rollback tool-specific; reject name-based equivalence.

## Anti-Patterns

- Treat a clean preview as execution approval, live convergence proof, or proof that unknowns are harmless.
- Rename or remove an address without proving move, import, replacement, destruction, orphaning, duplication, and remote identity.
- Present targeted operation evidence as the complete desired-state outcome.
- Call source rollback complete while state, resources, privileges, routes, secrets, or external effects remain changed.

## Stop Conditions

- Escalate unknown target, state owner, lock, effective state, version, identity, destruction, privilege, exposure, secrets, or recovery authority.
- Stop before production apply, state rewrite, import, forced replacement, destroy, deploy, release, rollback approval, or irreversible mutation.

## Output Contract

- target and state authority proposal limits identity and graph effects destruction sensitive outcomes recovery validation proof limits and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [state plan and drift contracts](references/state-plan-and-drift-contracts.md) | targeted | State authority locking drift unknown values or proposal freshness differs by the selected tool | One bounded source change preserves recorded and effective state without tool-specific proposal interpretation | analysis-agent, task-agent, review-agent | decision-record, proof-limit, residual-risk |
| [identity destruction and recovery contracts](references/identity-destruction-and-recovery-contracts.md) | targeted | Resource identity targeting replacement destruction protection recovery or secret exposure differs by the selected tool | No identity destructive sensitive or recovery outcome can change | analysis-agent, task-agent, review-agent | decision-record, proof-limit, residual-risk |
