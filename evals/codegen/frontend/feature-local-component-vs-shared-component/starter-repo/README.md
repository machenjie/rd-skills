# Starter Repo

## Stack

React TypeScript app with feature folders, shared design primitives, and
Testing Library component tests.

## Initial State

Billing settings renders account and invoice controls. The app has generic
`Card`, `Button`, and `Banner` primitives, but no shared product-tour component.
Dismissal state for billing-only tours does not exist yet.

## Files

- `src/features/billing/BillingSettings.tsx` renders the settings page.
- `src/features/billing/BillingTour.tsx` is available for feature-local UI.
- `src/features/billing/__tests__/BillingSettings.test.tsx` covers page render.
- `src/design/Banner.tsx` and `src/design/Button.tsx` expose shared primitives.
- `src/store/appStore.ts` owns global app state and should not receive billing-only state.

## Constraints

Billing-specific behavior should stay under `features/billing`. Shared design
components must remain business-neutral. Tests should use user-observable roles,
names, and interactions.
