---
name: test-data-management
description: "`analysis-agent`/`task-agent`/`review-agent`: use when fixtures, factories, seeds, isolation, cleanup, or sensitive test-data rules change; skip when test data is unaffected."
---

# test-data-management

## Registry Trigger

**Use when**

- manage fixtures factories seeded data isolation cleanup and sensitive data rules

**Do not use when**

- no task-local test data management decision is required

## Skill Role

Own fixture meaning, determinism, isolation/cleanup, relationships, sensitive-data controls, and freshness; exclude portfolio, database, and environment decisions.

## High-Value Rules

- Build the smallest fixture for the named failure mechanism and oracle.
- Define controls for oracle-affecting time, randomness, IDs, order, locale, and external responses.
- Define namespace and cleanup ownership across commit, asynchronous, and parallel effects.
- Select synthetic or approved minimized data that excludes production secrets and personal records.
- Bind schema, fixture, dependency, and environment versions; refresh after oracle-affecting changes.

## Anti-Patterns

- Local success substituted for evidence of the test data management contract.

## Stop Conditions

- Stop without an owned namespace or shared-safe cleanup.
- Stop on unapproved sensitive data, unreconciled asynchronous effects, or ambiguous drift.

## Output Contract

- test-data decision with failure-focused fixtures, deterministic generation, isolation and ownership, relationship integrity, sensitive-data controls, cleanup behavior, freshness evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | fixture ownership isolation privacy or cleanup mechanisms remain undecided | one deterministic owned fixture strategy covers the changed boundary | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | tests change fixtures randomness time sensitive data or external cleanup | test data remains deterministic isolated private and cleanup-safe | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | fixture ownership isolation or privacy claims need fresh proof | current factories cleanup paths and parallel tests prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
