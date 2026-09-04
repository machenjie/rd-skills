---
name: design-system-rules
description: "`analysis-agent`/`task-agent`: use when tokens, components, responsive behavior, accessibility, or variants need consistency rules; skip when UI system rules are unaffected."
---

# design-system-rules

## Registry Trigger

**Use when**

- apply design tokens component conventions spacing typography and interaction rules

**Do not use when**

- no task-local design system rules decision is required

## Skill Role

Define token semantics, component and variant fit, interaction-state consistency, responsive behavior, accessibility hooks, escape boundaries, and design-system evidence. Exclude product flow and implementation.

## High-Value Rules

- **Start from semantic intent and current system authority.** Map the needed role, emphasis, state, density, motion, and interaction to owned tokens, components, variants, and usage guidance before adding new surface.
- **Reuse by behavior, not visual resemblance.** Extend an existing component when interaction semantics, accessibility contract, state model, and ownership align. A distinct primitive is required when reuse would overload meaning or couple unrelated consumers.
- **Keep variants finite and composable.** Give each variant a named semantic axis, compatible state combinations, and an owner; reject prop combinations that create implicit component forks or contradictory behavior.
- **Preserve complete interaction and accessibility states.** Cover focus, hover, pressed, selected, disabled, loading, error, high contrast, reduced motion, keyboard behavior, labeling, and announcement where the affected component supports them.
- **Derive responsive behavior from content and container constraints.** Define wrapping, truncation, reflow, touch target, zoom, text expansion, and localization behavior using current supported viewport and content evidence.
- **Make exceptions explicit and recoverable.** Bound local overrides by reason, affected surface, fallback, ownership, and convergence trigger so an exception does not silently become a parallel system.
- **Validate visual and behavioral compatibility.** Compare affected states and consumers with focused interaction, accessibility, and visual evidence, including regression limits for uninspected surfaces.

## Anti-Patterns

- Add a token, component, or variant because a single screen looks different without proving reusable semantic meaning.
- Encode product-specific business state into a generic primitive or expose unrestricted styling that bypasses system contracts.
- Treat a static happy-path screenshot as proof for interaction, accessibility, responsive, theme, or localization behavior.

## Stop Conditions

Escalate when current design-system authority is unclear, reuse would change consumer semantics, a new primitive lacks ownership, or accessibility behavior cannot be specified. Also escalate when responsive or localized content cannot be exercised, or a broad shared-surface change lacks regression evidence.

## Output Contract

- design-system decision with semantic intent, token and component mapping, variant and state contract, responsive and accessibility behavior, bounded exceptions, validation evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Shared component, variant, token, or interaction choices compete | A feature-local layout does not alter shared semantics | analysis-agent, task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | System changes accessibility, responsiveness, variants, or API compatibility | No shared component or token contract changes | analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Design-system claims require current stories, screenshots, or accessibility reports | No reuse, responsive, or accessibility claim awaits proof | analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
