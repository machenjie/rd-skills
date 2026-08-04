---
name: prototype-description
description: "`analysis-agent`/`task-agent`: use when a prototype resolves hierarchy, interaction, failure, responsive, or accessibility uncertainty; skip visual-only polish."
---

# prototype-description

## Registry Trigger

**Use when**

- A prototype must resolve a named decision uncertainty about hierarchy, content, action, interaction, validation, failure, responsive behavior, accessibility, or reuse.
- A bounded product surface needs enough fidelity and evidence limits for review, handoff, or a next implementation decision.

**Do not use when**

- The open decision is product intent, a multi-page journey, information taxonomy, detailed state modeling, component governance, or visual styling alone.
- No prototype decision or evidence question changes.

## Skill Role

Describe a decision-oriented prototype with named uncertainty, bounded fidelity, hierarchy, interaction failures, responsive and accessibility obligations, reuse choices, and evidence limits.

## High-Value Rules

- Start with the uncertainty, changed decision, evidence owner, and required fidelity.
- Bound the surface by actor, goal, trigger, preconditions, exit, assumptions, and excluded behavior.
- Classify placeholder copy, invented data, and implied permissions as explicit assumptions.
- Define trigger, feedback, validation, persistence, cancellation, retry, undo, and outcome for relevant actions.
- Include only reachable states whose meaning or next action differs.
- Define reading order, reflow, overflow, input method, and focus for scoped viewport conditions.
- Define semantics, accessible names, keyboard behavior, announcements, and color-independent meaning.
- Do not report prototype review as accessibility certification.

## Anti-Patterns

- Visual polish, a component library, or a preferred tool leads before the uncertainty and decision owner are named.
- A generic loading, empty, error, success, and disabled catalog appears without reachable triggers or different actions.
- A new component is invented without a design-system gap, reuse decision, and owner.
- A screenshot, prototype walkthrough, checklist, or stakeholder approval is reported as production behavior, accessibility conformance, or implementation validation.

## Stop Conditions

- Route product intent, actors, journeys, information grouping, routes, and detailed states to their owners.
- Route components, design-system rules, implementation, acceptance, and executable proof to their specialist owners.

## Output Contract

- prototype decision brief with uncertainty, fidelity, hierarchy, interaction and failure behavior, responsive and accessibility obligations, reuse decision, evidence, handoffs, proof limits, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Prototype uncertainty hierarchy interaction failure responsive accessibility or reuse choices remain decision-relevant | Current surface contracts and scoped evidence settle the named prototype question and handoffs | analysis-agent, task-agent | option-comparison, selected-approach |
