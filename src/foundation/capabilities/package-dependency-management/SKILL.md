---
name: package-dependency-management
description: "`analysis-agent`/`task-agent`/`review-agent`: use when package managers, lockfiles, additions, upgrades, removals, licenses, or supply-chain risks change; skip unrelated work."
---

# package-dependency-management

## Registry Trigger

**Use when**

- package manager lockfile workspace monorepo dependency upgrade dependency removal new package license provenance transitive dependency supply chain generated files native extension SDK library public API

**Do not use when**

- no task-local package dependency management decision is required

## Skill Role

Define package authority, necessity, graph effects, lockfile integrity, lifecycle code, compatibility, provenance, licensing, and removal proof. Exclude vulnerability acceptance and pipeline trust.

## High-Value Rules

- Keep package decisions within repository authority and load the command-map, checklist, and evidence References only for their active decision problems.
- Preserve current compatibility and graph obligations.
- Route vulnerability, policy, legal, public-contract, credential, and release-registry decisions to owners.

## Anti-Patterns

- Reject manual locks, unjustified packages, unrelated graph churn, and import-only removal proof.

## Stop Conditions

Escalate when package authority is ambiguous, the resolved graph is not reproducible, a lifecycle hook or binary lacks acceptable provenance, or license obligations conflict. Also escalate when compatibility impact is unknown, removal evidence is incomplete, or the change affects public contracts, credentials, release registries, or a reachable security finding.

Stop package-risk closure until `dependency-vulnerability-scanning` or the accountable policy or legal owner returns an accepted decision for the selected graph and artifact scope; otherwise return the evidence gap and proof limit.

## Output Contract

- dependency decision with repository authority, capability rationale, resolved-graph delta, lockfile evidence, lifecycle and provenance review, compatibility effects, and removal proof
- package-risk evidence handoff with graph and artifact scope, scanner, license, and provenance artifacts, accepted specialist or policy-owner decision, exceptions, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | dependency change affects alternatives lockfiles transitive risk licenses or platforms | manifest and resolved dependency graph remain unchanged | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [ecosystem command map](references/ecosystem-command-map.md) | targeted | package manager lockfile workspace or dependency commands are uncertain | repository commands are explicit and the dependency graph is unchanged | analysis-agent, task-agent, review-agent | validation-plan, proof-limit, evidence-gap |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | provenance vulnerability license or reproducibility claims need current artifacts | fresh graph scans lockfiles and builds prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
