---
name: data-api-contract-changer
description: "Analyze an API, schema, migration, or compatibility decision with `analysis-agent`, or implement its bounded contract change with `task-agent`. Do not select it when no data or public-contract surface is affected."
---

# data-api-contract-changer

## Role

Own evidenced data and public-contract transitions.

- **Analysis mode (`analysis-agent`):** Decide compatibility and coexistence.
- **Task mode (`task-agent`):** Apply the accepted transition.

## When To Use

- API contract change
- schema or migration change

## Do Not Use

- no data or public contract impact
- unrelated read-only analysis

## Required Inputs

- contract evidence and compatibility requirements
- **Analysis mode (`analysis-agent`):** consumer inventory, deployed versions, and current schema or API behavior.
- **Task mode (`task-agent`):** accepted contract decision, producer, consumer, migration, and rollback checks.

## Professional Decision Rules

- Classify the contract, consumers, deployed versions, and coexistence.
- Select an additive, versioned, or staged transition from compatibility and rollback evidence.
- Preserve null, default, generated, replay, and old-client semantics.
- Verify producers, generated surfaces, and known consumers.
- Record unverified consumers.

## High-Value Gotchas

- An additive field can still break strict, exhaustive, generated, or default-sensitive consumers.
- Rollback cannot restore contracted data or a stranded consumer automatically.

## Execution Checklist

1. Inventory the authoritative contract, producers, consumers, deployed versions, and generated surfaces.
2. Choose one transition and state coexistence, migration, validation, and rollback limits.
3. Limit loading to the active decision's named Reference, with index/catalog paths excluded.
4. Prove producer and known-consumer behavior after the final material edit.
5. Record unknown consumers, external authority, and irreversible limits.
6. **Analysis mode:** Return the selected transition and proof limits.
7. **Task mode:** Apply the accepted transition at the producer and consumer owners.

## Stop / Escalation Conditions

- Stop on unresolved compatibility, consumer coverage, generated lineage, migration, rollback, validation, or authority.

## Output Contract

- contract transition, consumer impact, and compatibility evidence
- **Analysis mode (`analysis-agent`):** contract transition, consumer impact, and migration and rollback model.
- **Task mode (`task-agent`):** producer and consumer changes, compatibility evidence, and unverified consumers.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs concrete contract, pagination, migration, rollback, deprecation, and observability coverage | Consumer proof, generated diff, or performance/rollback tradeoff is the core risk | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on consumer proof, generated artifact diff, migration/rollback evidence, deprecation/deletion, or stale contract validation | High-level routing is enough and evidence is not being closed | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing data api contract changer references require dependency, conflict, or output-fragment selection | the data api contract changer root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | A schema, API, event, version, migration, list/expansion, filter, or compatibility design has a material consumer, data-growth, or recovery tradeoff | The change is demonstrably additive and bounded with no affected consumer, storage, query, migration, or coexistence choice | analysis-agent, task-agent | selected-approach, residual-risk |
