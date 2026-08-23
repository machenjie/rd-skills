---
name: domain-object-identification
description: "`analysis-agent`/`task-agent`/`review-agent`: classify domain identity, values, aggregates, lifecycle, invariants, writers, and relationships; skip layer-derived nouns."
---

# domain-object-identification

## Registry Trigger

**Use when**

- Domain category, identity, value equality, lifecycle, aggregate, invariant, writer authority, relationship, or boundary mapping needs a decision.
- An implementation or actual diff may confuse a domain object with a DTO, table, UI label, function, helper, or module.

**Do not use when**

- no task-local domain object identification decision is required

## Skill Role

Establish where identity, lifecycle, invariants, ownership, permissions, persistence, events, and tests belong. Separate domain concepts from tables, API resources, DTOs, UI labels, generated schemas, and read models.

## High-Value Rules

- Reject naming and proximity observations as domain-authority evidence.
- Select the category or checklist Reference for disputed classification and multi-part closure.
- Load the evidence Reference for current writer, schema, and consumer proof.

## Anti-Patterns

- Local success substituted for evidence of the domain object identification contract.

## Stop Conditions

- Route language reference, value, equality, hash, and aliasing semantics to the language Skill.
- Route object-versus-function/module and accepted-owner method placement to `implementation-structure-design`.
- Route unclear invariants/lifecycle, actor rights, persistence, transfer/event contracts, and concurrent cross-aggregate ownership to their named business-rule, state, permission, data, schema/event, or consistency owners.

Escalate when object boundaries affect consistency, tenant ownership, money movement, regulated records, audit history, migration design, external API resources, or event semantics.

Escalate when term renaming or reuse can change permissions, data ownership, API/event meaning, metrics, audit interpretation, or cross-service writer authority.

Escalate when graph or source search finds the same term used by multiple modules with different lifecycle, identity, or owner semantics.

## Output Contract

- Domain-object decision with classification and rejected alternatives; entity identity; value equality, immutability, and replacement semantics; lifecycle; aggregate and invariants; writer authority; relationships and mappings; evidence; proof limits; and residual risks.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Object category, aggregate boundary, or writer authority remains disputed | Identity, ownership, and lifecycle are already explicit | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Object changes identity, cardinality, invariants, mapping, or tenant scope | No domain object or relationship changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Object claims depend on fresh writers, schemas, and consumer evidence | No ownership or object-category claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
