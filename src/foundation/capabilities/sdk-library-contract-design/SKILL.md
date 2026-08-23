---
name: sdk-library-contract-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when SDK/library APIs, semver, compatibility, deprecation, or migration changes; skip without library-contract impact."
---

# sdk-library-contract-design

## Registry Trigger

**Use when**

- SDK library generated client package public API internal library semver deprecation examples migration consumer contract tests publication

**Do not use when**

- no task-local sdk library contract design decision is required

## Skill Role

Own contract compatibility, generated lineage, adoption, and consumer proof.

## High-Value Rules

- Classify exported types, defaults, errors, runtimes, packaging, and behavior.
- Bind source, generator, configuration, artifact, and reviewed generated diff.
- Select adoption and rollback from current consumer evidence.
- If the library decision remains active, load only its named Reference.

## Anti-Patterns

- Local success substituted for packed-consumer evidence.

## Stop Conditions

Stop on unknown surface, consumers, lineage, adoption, rollback, or publication authority.

## Output Contract

- library contract decision with consumed surface, compatibility classification, generated lineage, mixed-version adoption, consumer proof, release handoffs, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | versioning generation compatibility or release mechanisms remain undecided | ecosystem policy and consumer contract select one release path | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects exports types defaults runtimes generation consumers or deprecation | public package and generated surfaces remain unchanged | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | semver generation consumer or provenance claims need fresh artifacts | API diffs fixture consumers and packed examples prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
