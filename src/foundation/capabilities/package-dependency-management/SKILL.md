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

- **Follow the repository's package authority.** Identify manifest, lockfile, workspace root, resolution policy, supported runtimes, registry configuration, and generated-file ownership before changing dependencies.
- **Justify capability before package choice.** Compare reuse already present, platform support, implementation cost, maintenance status, transitive surface, runtime weight, license, and security consequence against the task-local need.
- **Review the resolved graph, not the requested line alone.** Inspect added, removed, deduplicated, downgraded, platform-specific, optional, peer, and transitive packages plus runtime, build, and deployment effects.
- **Treat lifecycle code as executable supply chain.** Inspect install hooks, build plugins, generators, native extensions, downloaded binaries, registry provenance, checksums, and credential exposure according to current trust policy.
- **Bound compatibility from current consumers.** Check runtime floors, public types, module format, generated output, configuration, binary interfaces, and peer ranges before accepting an addition or upgrade.
- **Keep lockfile change attributable.** Regenerate through the repository-owned mechanism, separate expected graph movement from unrelated churn, and preserve evidence connecting manifest intent to resolved output.
- **Prove removal across all consumption paths.** Scan source, tests, scripts, generated code, configuration, plugins, dynamic loading, deployment assets, and transitive reliance; distinguish unused direct declaration from still-needed resolved dependency.

## Anti-Patterns

- Edit a lockfile manually, regenerate it from the wrong workspace or runtime, or accept unrelated resolver churn without explanation.
- Add a package for trivial convenience while ignoring existing capability, transitive cost, lifecycle code, or long-term ownership.
- Declare removal complete from source imports alone while scripts, generators, configuration, plugins, or runtime loading still depend on it.

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
