---
name: ci-cd
description: "`analysis-agent`/`task-agent`/`review-agent`: use when CI/CD checks, artifacts, deployment gates, IaC, or Helm behavior changes; skip when pipelines are unaffected."
---

# ci-cd

## Registry Trigger

**Use when**

- hosted pipeline change affects triggers, required checks, credentials, artifacts, affected-work selection, promotion, IaC or Helm plans, or rollback

**Do not use when**

- only local build commands change and hosted pipeline or promotion behavior is unaffected

## Skill Role

Define hosted-pipeline enforcement, artifact identity, deployment authority, partial failure, and rollback limits. Exclude local builds and cluster semantics.

## High-Value Rules

- Define required checks by trigger, scope, protected target, outcomes, retry, and bypass authority; green does not prove provider enforcement.
- Bind revision and behavior inputs to build identity, provenance, registry and promoted artifacts, and rollback target; rebuild only under an explicit equivalence contract.
- Model event and runner trust before credentials: forks, reusable workflows, third-party actions, cache/artifact poisoning, permissions, environment, and protected branch.
- Include owners, dependents, contracts, generated inputs, toolchains, and behavior config in affected-work and cache selection; fall back safely when exclusion is unproven.
- Bind IaC, Helm, GitOps, or deploy plans to target and state, authority, concurrency, destructive effects, partial failure, and recovery limits.
- Preserve the redacted first failure and available artifacts across retry or quarantine. Replacements define signal, owner, remediation, and promotion consequence; retry-to-green does not restore proof.
- Faithfully encode the accepted approval, exposure, observation, stop, and post-deploy contract from `delivery-release-gate` and the accepted recovery contract from `release-rollback`.

## Anti-Patterns

- Local simulation does not prove hosted permissions, protection, approvals, runner identity, or provider enforcement.
- Upload does not prove deployed revision, config, migration, or runtime state.
- A clean plan or render does not prove apply authority, provider behavior, reversibility, or partial recovery.
- Masking, broad permissions, mutable actions, continue-on-error, or silent retries can hide a boundary.

## Stop Conditions

- Escalate credentials exposed to untrusted code, unauthorized bypass, ambiguous release identity, unrecoverable destruction, or unauthorized live deployment.
- Stop when required provider enforcement or artifact/deployment identity has only local static evidence.
- Stop when an applicable accepted release or recovery contract is absent or cannot be represented by the provider.
- Route release or recovery decision derivation to its owning gate.

## Output Contract

- State enforcement, artifact identity, runner trust, affected work, mutation and rollback boundaries, provider proof, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | pipeline change crosses check credential artifact mutation or rollback boundaries | pipeline behavior and promotion boundaries are unchanged | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | hosted enforcement artifact identity permission plan or provider-state claims need fresh proof | no pipeline or provider-state claim awaits validation | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
| [pipeline benchmarks](references/pipeline-benchmarks.md) | benchmark-pattern | an accepted release and recovery contract leaves provider enforcement supply-chain IaC Helm monorepo or pipeline-evidence mechanisms open | the accepted contract is absent or an open rollout recovery decision remains or one provider mechanism is fixed | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
