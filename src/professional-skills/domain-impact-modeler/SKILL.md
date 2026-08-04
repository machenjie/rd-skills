---
name: domain-impact-modeler
description: "Use `analysis-agent` to identify domain ownership, invariants, state transitions, and cross-context effects when rules change or ownership is unclear. Skip presentation-only or question-only work with no domain behavior."
---

# domain-impact-modeler

## Role

Support `analysis-agent` in locating domain ownership, invariants, transitions,
and cross-context effects.

## When To Use

- business invariant change
- domain ownership unclear

## Do Not Use

- presentation only with no domain behavior
- question only

## Required Inputs

- intent slice
- domain source evidence
- owning module candidates

## Professional Decision Rules

- Locate the aggregate or module that owns the invariant; controllers, DTOs, and persistence records do not own business truth by default.
- State entities, value objects, identities, valid transitions, forbidden transitions, and decision authority.
- Protect monetary, permission, lifecycle, and cross-tenant invariants before choosing storage or API shape.
- Reuse existing domain language and reject duplicate models that split one invariant across owners.

## High-Value Gotchas

- Persistence shape is not the domain model.
- A transition without forbidden cases weakens the invariant.
- Money, permission, and tenant rules require exact ownership.

## Execution Checklist

1. Trace the changed rule to its vocabulary, authority, state transitions, and current owner.
2. Choose the aggregate or module that already owns the invariant's reason to change.
3. Verify forbidden transitions, consumers, historical impact, and cross-context dependency direction.
4. Stop placement when ownership or invariant evidence remains contradictory.

## Stop / Escalation Conditions

- Stop implementation planning when aggregate owner, rule authority, event consumers, permission boundary, historical-data impact, or bounded-context relationship is unknown.
- Stop "single-context" closure when a term, event, table, permission, report, or integration crosses a context without owner and dependency-direction evidence.
- Stop event/schema changes when versioning, replay/upcaster risk, consumer migration, and rollback or dual-read/write plan are absent.
- Stop domain claims that rely on summaries or search adjacency as fact instead
  of current source, explicit owner evidence, or validation.

## Output Contract

- owning module
- domain invariants
- rejected locations

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [business invariant evidence](references/business-invariant-evidence.md) | evidence-pattern | Business vocabulary, state transitions, calculations, or forbidden outcomes need explicit invariant proof | No domain invariant changes | analysis-agent | evidence-record, proof-limit, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | Aggregate, rule, event, permission, transition, audit, or consistency surfaces need a compact coverage check | The current source and tests already establish every relevant surface | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | A domain rule needs source-to-test, event-consumer, owner, freshness, or residual-risk evidence | The root output contract is sufficient for the bounded decision | analysis-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing domain impact modeler references require dependency, conflict, or output-fragment selection | the domain impact modeler root or a task-named reference already resolves selection | analysis-agent | reference-selection |
