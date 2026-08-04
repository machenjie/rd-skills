---
name: data-model-design
description: "`analysis-agent`/`task-agent`: use for persisted identity, relationship, ownership, lifecycle, cardinality, or invariants; skip repository, migration, and mapping-only work."
---

# data-model-design

## Registry Trigger

**Use when**

- design authoritative persisted records entities attributes relationships cardinality ownership lifecycle and enforceable invariants

**Do not use when**

- work is limited to repository mechanics, migration execution, transaction orchestration, consumer inventory, or DTO/model translation

## Skill Role

Define the smallest authoritative logical or schema model that represents business facts and prevents material invalid states. Exclude repository behavior, migration execution, transaction protocols, and cross-layer mapping.

## High-Value Rules

- **Authority before shape.** Record each changed fact's source of truth, mutation authority, lifecycle evidence, and uninspected writers.
- **Complete semantics.** State identity, cardinality, optionality, null/default meaning, lifecycle, history, and deletion behavior before selecting physical shape. Distinctions that change business behavior remain preserved.
- **Owned enforcement.** For each material invariant, choose the strongest boundary the current store and writer topology can honor. Name cross-record, cross-owner, or external-system races that remain.
- **Evidence-driven shape.** Choose normalization, embedding, derived state, and storage shape from named ownership, write, read, history, failure, and rebuild needs. Derived state names its authoritative source, lag tolerance, and reconciliation owner.
- **Compatible evolution.** State the conditions existing rows and mixed-version writers must satisfy. Hand data conversion, sequencing, rollback, and destructive rollout mechanics to `data-migration-design`.
- **Bounded claims.** Bound impact claims by inventorying affected schema, generated, job, report, and dynamic consumers; classify uninspected consumers and production distributions as unverified.

## Anti-Patterns

- Reject transport, form, or report shapes promoted to authoritative models without ownership, lifecycle, and invariant evidence.
- Reject ambiguous lifecycle/null states, shared mutation without authority, and derived state without rebuild and reconciliation ownership.
- Reject constraints or destructive shape changes that current rows or mixed-version writers cannot satisfy.
- Reject no-consumer claims based only on a source search.

## Stop Conditions

Stop when authority, identity, cardinality, or lifecycle evidence conflicts; regulated retention or deletion lacks an accountable owner; correctness depends on cross-owner atomicity; or unknown writers/consumers make compatibility unknowable. Source, fixture, and local validation evidence proves inspected paths, not production distribution, hidden writers, or external consumers.

## Output Contract

- Return an authoritative data-model decision: define identity, relationships, ownership, lifecycle, invariants, enforcement, evolution constraints, evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Storage fit ownership normalization history or enforcement mechanisms compete | The root rules and current authority select one bounded model | task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Model changes identity cardinality invariants lifecycle access deletion or mixed-version behavior | No authoritative entity relationship or storage contract changes | task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Authority invariant consumer evolution or migration claims need fresh proof | Current schemas writers consumers and validators prove each bounded claim | task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
