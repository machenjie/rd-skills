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

- Classify each candidate as entity, value object, aggregate root, child entity, resource, policy, boundary model, or read model from domain meaning and bounded-context evidence.
- Define entity identity across time, including natural or surrogate keys, tenant scope, external identifiers, uniqueness, and merge or split behavior.
- A value object has no independent identity. Define equality attributes and normalization, keep it immutable, and express change through replacement semantics.
- Make the aggregate root the entry point for aggregate updates and invariants. Derive its boundary from consistency and writer authority rather than joins, screens, or nesting.
- Record lifecycle, transitions, invariant owner, accepted and rejected writers, mutation entry points, permissions, persistence, and events.
- Record relationships, cardinality, optionality, reference direction, cross-aggregate identity references, and mappings to DTO, schema, table, event, provider, UI, and read-model surfaces.
- Return classification, rejected alternatives, ownership evidence, proof limits, and residual risks.
- Treat naming and proximity observations as insufficient evidence of domain authority.

## Anti-Patterns

- Reject ownership inferred only from names, proximity, or repository search.
- Confirm business owner, data owner, source of truth, tenant scope, mutation authority, and writer entry points from current evidence.
- Reject deep object nesting across aggregates unless the parent owns the child’s lifecycle and invariants.
- Keep cross-aggregate references by identity.
- Reject unowned cross-aggregate workflows; assign domain events, a process manager, compensation, or an explicit eventual-consistency decision.

## Stop Conditions

- Route language reference, value, equality, hash, and aliasing semantics to the language Skill.
- Route object-versus-function/module and accepted-owner method placement to `implementation-structure-design`.

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
