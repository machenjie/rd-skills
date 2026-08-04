---
name: data-api-contract-changer
description: "Analyze an API, schema, migration, or compatibility decision with `analysis-agent`, or implement its bounded contract change with `task-agent`. Do not select it when no data or public-contract surface is affected."
---

# data-api-contract-changer

## Role

Support `analysis-agent` and `task-agent` for bounded data and public-contract changes.

- **Analysis mode (`analysis-agent`):** Classify compatibility, migration, and coexistence requirements.
- **Task mode (`task-agent`):** Apply the accepted transition across producers and consumers.

## When To Use

- API contract change
- schema or migration change

## Do Not Use

- no data or public contract impact
- unrelated read-only analysis

## Required Inputs

- contract evidence
- compatibility requirements
- **Analysis mode (`analysis-agent`):** consumer inventory, deployed versions, and current schema or API behavior.
- **Task mode (`task-agent`):** accepted contract decision with producer, consumer, migration, and rollback checks.

## Professional Decision Rules

- Treat API, event, schema, error, and data formats as consumer contracts with explicit compatibility windows.
- Prefer additive evolution; use expand, migrate, verify, and contract ordering for stateful changes.
- Identify old/new coexistence, defaults, nullability, versioning, replay, and rollback behavior.
- Validate producers and consumers, not only the changed implementation.

## High-Value Gotchas

- A nullable or defaulted field can still break semantic compatibility.
- Rollback may fail after irreversible data contraction.
- Producer-only tests miss consumer breakage.

## Execution Checklist

1. Trace the changed field, schema, error, or event semantics through every known consumer.
2. Choose an additive, versioned, or staged transition from coexistence and rollback evidence.
3. Verify defaults, nullability, generated surfaces, replay, and old-client behavior.
4. **Analysis mode:** select a transition from consumer and coexistence evidence.
5. **Task mode:** apply the transition across generated and deployed consumer surfaces.
6. Stop when consumer coverage or rollback feasibility remains unknown.

## Stop / Escalation Conditions

- Stop implementation when compatibility class, known/unknown consumers, old-client behavior, generated artifact diff, migration order, rollback, validation command, or deprecation owner is implicit.
- Stop breaking changes that remove/rename/change type/semantics until versioning or expand/migrate/contract, migration guide, consumer notification, and rollback evidence are present.
- Stop schema or data changes when production table size, lock behavior, null/default semantics, old/new version skew, or rollback script is unknown.
- Stop external actions when generated clients, production data, external
  consumers, mobile lag, audit data, or releases require additional authority.
- Require current permission, redaction, approval, and freshness evidence before proceeding.

## Output Contract

- **Analysis mode (`analysis-agent`):** contract transition; consumer impact; migration and rollback model.
- **Task mode (`task-agent`):** producer and consumer changes; compatibility evidence; unverified consumers.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs concrete contract, pagination, migration, rollback, deprecation, and observability coverage | Consumer proof, generated diff, or performance/rollback tradeoff is the core risk | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on consumer proof, generated artifact diff, migration/rollback evidence, deprecation/deletion, or stale contract validation | High-level routing is enough and evidence is not being closed | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing data api contract changer references require dependency, conflict, or output-fragment selection | the data api contract changer root or a task-named reference already resolves selection | analysis-agent, task-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | A schema, API, event, version, migration, list/expansion, filter, or compatibility design has a material consumer, data-growth, or recovery tradeoff | The change is demonstrably additive and bounded with no affected consumer, storage, query, migration, or coexistence choice | analysis-agent, task-agent | selected-approach, residual-risk |
