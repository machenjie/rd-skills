---
name: layered-architecture-design
description: "`analysis-agent`/`task-agent`: use when presentation, application, domain, or infrastructure ownership/dependencies change; skip without a layering decision."
---

# layered-architecture-design

## Registry Trigger

**Use when**

- design presentation application domain infrastructure and persistence layering

**Do not use when**

- no task-local layered architecture design decision is required

## Skill Role

Define layer responsibilities, dependency direction, domain independence, orchestration, adapter boundaries, cross-cutting placement, and layer evidence. Exclude architecture-style selection and module decomposition.

## High-Value Rules

- **Define layers by responsibility and authority.** Distinguish transport or presentation, application orchestration, domain decisions, and infrastructure capabilities using actual ownership rather than folder names.
- **Point dependencies toward stable policy.** Keep business rules independent of delivery and storage mechanisms, and represent required external capabilities through contracts owned at the appropriate inner boundary.
- **Keep orchestration distinct from domain decisions.** Let application code coordinate use cases, transactions, identity context, and effects while domain owners enforce invariants and infrastructure adapters implement external mechanisms.
- **Translate at boundaries.** Map transport, persistence, provider, event, and framework models to owned internal meaning so external schema or lifecycle changes do not leak across layers silently.
- **Place cross-cutting behavior at the decision point.** Align validation, authorization, transactions, retries, logging, caching, and error translation with the layer holding the required context and authority.
- **Avoid ceremonial pass-through.** Retain a layer or interface only when it protects a real policy, substitution, ownership, lifecycle, compatibility, or test boundary.
- **Prove dependency and behavior effects.** Inspect imports, construction, runtime calls, state and side effects, tests, generated code, and bypass paths, then state repository and runtime limits.

## Anti-Patterns

- Put business rules in controllers, persistence models, framework callbacks, or adapters because those locations already have data.
- Mirror identical models and pass-through methods across layers without protecting a semantic boundary.
- Infer architecture from directory layout while runtime dependencies, callbacks, service location, or generated wiring point elsewhere.

## Stop Conditions

Escalate when responsibility or authority is ambiguous, domain logic depends directly on volatile infrastructure, or transactions or permissions span layers without an owner. Also escalate when a proposed layer lacks a decision boundary, or actual dependency direction cannot be established.

## Output Contract

- layered-architecture decision with responsibilities, dependency direction, domain and orchestration boundary, adapters, cross-cutting placement, evidence, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | placement transaction or failure translation has competing layer choices | current dependency direction and ownership select one layer placement | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change crosses presentation application domain infrastructure or adapter boundaries | owner-internal change preserves all established layer contracts | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | layer dependency transaction or exception claims need current proof | post-edit imports tests and architecture checks prove each claim | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
