---
name: page-component-decomposition
description: "`analysis-agent`/`task-agent`: use when page components, props, state ownership, reuse, or decomposition boundaries change; skip when no component-structure decision exists."
---

# page-component-decomposition

## Registry Trigger

**Use when**

- decompose page into components responsibilities props and reusable boundaries

**Do not use when**

- no task-local page component decomposition decision is required

## Skill Role

Define component responsibility, state and effect ownership, data-flow contracts, reuse boundaries, rendering and interaction consequences, and decomposition evidence. Exclude product-flow design and framework implementation.

## High-Value Rules

- **Decompose by ownership and change reason.** Group behavior that shares state, lifecycle, policy, or release responsibility, and split when distinct responsibilities can evolve behind a stable contract.
- **Place state at the narrowest common owner.** Keep local interaction state near its consumers and share it only across real coordination boundaries. Server or authoritative state semantics remain unduplicated in view components.
- **Make component contracts semantic.** Pass domain-relevant values, actions, status, and errors with clear optionality and ownership; avoid broad context, mutable objects, or callback bags that hide dependencies.
- **Separate orchestration from presentation where it changes evidence.** Keep fetching, mutation, routing, permission context, and effect coordination outside reusable presentation units when separation enables clearer ownership and tests.
- **Reuse only across aligned behavior.** Extract a shared component when interaction semantics, accessibility, visual states, and expected evolution match; prefer local duplication over a premature abstraction joining unrelated change reasons.
- **Preserve rendering and interaction boundaries.** Account for loading, error, empty, permission, responsive, focus, hydration, and expensive-render behavior that may cross the proposed split.
- **Prove integration after the split.** Verify public behavior, state transitions, effect ordering, accessibility, and affected consumers, while stating surfaces and framework behavior left uninspected.

## Anti-Patterns

- Split by file length, markup count, or visual boxes without identifying ownership and independent change.
- Lift state globally for convenience or hide required data and effects behind implicit context.
- Create a generic component from one consumer, then accumulate flags that encode separate products or workflows.

## Stop Conditions

Escalate when state authority or effect ownership is unclear, the split crosses permission or transaction boundaries, or reuse couples independent owners. Also escalate when rendering semantics are uncertain, or current tests cannot distinguish behavior preservation from structural movement.

## Output Contract

- component decomposition decision with responsibility boundaries, state and effect owners, semantic contracts, reuse rationale, rendering consequences, integration evidence, and residual risks

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | responsibility state ownership reuse or orchestration admits competing decompositions | one existing component boundary fully owns the changed behavior | task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | page change mixes workflow state side effects rendering or permissions | local component change preserves established responsibilities and state ownership | task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | reuse ownership accessibility or decomposition claims need current proof | current consumers stories tests and source prove each claim | task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
