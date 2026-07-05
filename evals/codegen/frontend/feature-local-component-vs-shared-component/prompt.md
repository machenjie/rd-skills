# Benchmark Prompt

## Task

Add a billing settings product-tour banner and dismissal state. Decide whether
the component and hook should stay feature-local or become shared UI.

## Context

The starter repo has a `features/billing` area and a small design system. The
tour copy, visibility condition, and dismissal state are specific to billing.
AI-generated code proposes `components/common/ProductTourCard.tsx` and
`hooks/useProductTour.ts`.

## Requirements

- Keep billing-specific behavior feature-local unless a real shared contract exists.
- Reuse existing design system primitives instead of creating a new shared card.
- Keep state scope as narrow as possible.
- Add tests for render, dismiss, and rerender persistence behavior.
- Include an Implementation Structure Plan covering component, hook, state, and test placement.

## Constraints

- Do not put billing-specific copy or rules in `components/common`.
- Do not introduce global state for one feature.
- Do not scatter API or persistence calls directly through presentational components.

## Deliverables

- Billing feature component or local composition using existing primitives.
- Feature-local hook or state logic if needed.
- Component tests or feature tests for dismissal behavior.
- Structure rationale for feature-local versus shared placement.

## Completion Evidence

- Tests prove user-visible billing tour behavior and dismissal.
- Diff shows no billing business rule in common components or generic hooks.
- Structure plan names reuse candidates and rejected shared component alternative.
