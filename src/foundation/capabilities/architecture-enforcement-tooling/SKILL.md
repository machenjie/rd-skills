---
name: architecture-enforcement-tooling
description: "`analysis-agent`/`task-agent`/`review-agent`: use when architecture rules need lint, dependency, type, or CI enforcement; skip when no enforcement decision is required."
---

# architecture-enforcement-tooling

## Registry Trigger

**Use when**

- architecture enforcement tooling, import boundary check, cycle detection, public private export, forbidden dependency lint, type strictness, dead code, complexity threshold, generated code exclusion, CI, ArchUnit, Dependency Cruiser, import linter, eslint boundaries, go vet, staticcheck

**Do not use when**

- no task-local architecture enforcement tooling decision is required

## Skill Role

Turn accepted architecture and module-boundary decisions into deterministic checks, repairable failures, bounded exceptions, CI gates, and ratcheted baselines.

## High-Value Rules

- Map each enforced rule to an accepted architecture or module-boundary decision and a repairable failure message.
- Select local, pre-merge, CI, or report-only placement from consequence and migration state; label unenforced rules as advisory.
- Bound generated-code and other exceptions by owner, reason, scope, and review trigger, and prove representative rejection behavior.
- Select baseline, ratchet, staged enforcement, or immediate blocking from current violations and migration risk rather than breaking unrelated work.
- Preserve intentional public contracts and classify existing violations as block, owned baseline, bounded suppression, or deletion.
- Choose tooling that can express the rule in the current language, graph, and runner, and gate new dependencies by supply-chain and reproducibility evidence.
- Require current rule inventory, negative fixture, exception policy, and changed-path coverage before treating a green command as enforcement proof.

## Anti-Patterns

- Enforcing import direction while omitting cycles, public/private export expansion, forbidden UI-to-data/domain-to-infrastructure/feature-to-feature/test-to-production edges, or cross-module internals leaves accepted architecture decisions unchecked.
- Dead-code detection that ignores reflection, generated entry points, CLI commands, migrations, or framework registration produces unsafe deletions or permanent false positives.
- One complexity threshold across local language tooling and generated code punishes the wrong surface instead of enforcing an owned rule.
- A nondeterministic or undocumented CI command, or fast local feedback with no CI source of evidence, makes enforcement optional.
- Report-only migration with no owned baseline and ratchet preserves every existing violation indefinitely.
- Suppressions without owner, reason, scope, and expiry or review trigger become silent architecture exceptions.
- Generic lint failures that omit the violated rule and intended replacement path cannot guide repair.

## Stop Conditions

Escalate to `delivery-release-gate` when new CI gates affect release flow. Escalate to `architecture-impact-reviewer` when enforcement reveals ambiguous ownership. Escalate to `ai-code-review-refactor` when generated code or AI-produced files need exemptions that could hide real violations.

Escalate to `security-privacy-gate` when a rule touches authentication, authorization, secrets, permission boundaries, or supply-chain-sensitive tooling. Escalate to `package-dependency-management` when enforcement requires a new package, plugin, action, binary, container image, or lockfile change. Escalate to `consumer-impact-analysis` before blocking or removing public exports that may be used outside local search scope.

## Output Contract

- Return an Architecture Enforcement Plan: list rules, tool and CI choices, failure examples, generated-code exceptions, migration, ownership, and residual gaps

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Multiple enforcement tools or ratchet strategies fit the rule | Existing CI tooling already expresses the accepted rule | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Enforcement crosses exports, generated code, exceptions, or migration baselines | One existing check covers the rule without exemptions | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Enforcement claims depend on fresh graph, config, or CI results | No enforceability or drift claim is being closed | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
