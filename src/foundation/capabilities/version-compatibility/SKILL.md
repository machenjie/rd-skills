---
name: version-compatibility
description: "`analysis-agent`/`task-agent`/`review-agent`: use when API, schema, event, or behavior changes need compatibility, deprecation, rollout, or migration; skip without version impact."
---

# version-compatibility

## Registry Trigger

**Use when**

- assess backward compatibility deprecation version negotiation and client migration

**Do not use when**

- no task-local version compatibility decision is required

## Skill Role

Define consumers, compatibility dimensions, mixed-version behavior, retirement, rollback readability, and evidence. Exclude contract design, migration execution, and release authority.

## High-Value Rules

- Inventory evidence-backed consumers, retained state/messages, and version skew.
- Classify mixed-version behavior, migration, rollback readability, and retirement across the affected structural and semantic compatibility dimensions.
- Load the named benchmark, checklist, or evidence Reference according to the open output.

## Anti-Patterns

- Local success substituted for evidence of the version compatibility contract.

## Stop Conditions

- Stop when consumers or skew are unknown, versions cannot coexist, rollback cannot interpret new state, long-lived clients lack adoption, or retirement evidence is unavailable.
- Escalate compatibility that affects public, regulated, financial, permission, or irreversible behavior.

## Output Contract

- compatibility decision with consumer inventory, compatibility dimensions, mixed-version matrix, migration mechanism, retirement evidence, rollback limits, proof gaps, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | mixed-version failures lack negative-path coverage | compatibility tests cover triggered boundaries | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [compatibility benchmarks](references/compatibility-benchmarks.md) | benchmark-pattern | migration policy remains unresolved | no mixed-version consumers are affected | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | consumer evidence may be stale | current artifacts prove consumer behavior | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
