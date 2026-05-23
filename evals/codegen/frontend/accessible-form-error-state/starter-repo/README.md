# Starter Repo

## Stack

TypeScript React component with existing form primitives, fetch helper, and
Testing Library style component tests. The starter uses strict TypeScript and a
small local validation helper.

## Initial State

The email change form submits values and renders server error text in a generic
block. Inputs lack `aria-describedby`, invalid fields are not marked, and tests
only assert that the submit callback is called on a happy path.

## Files

- `src/account/EmailChangeForm.tsx` renders fields and submit state.
- `src/account/emailValidation.ts` contains placeholder validation helpers.
- `src/account/api.ts` wraps the backend email change endpoint.
- `src/account/__tests__/EmailChangeForm.test.tsx` covers the current happy path.
- `src/design/FormField.tsx` exposes the existing form primitive.

## Constraints

Stay within the existing design primitives and avoid global styling changes.
Preserve form values across failed submits. Tests should assert DOM semantics
through user observable queries instead of implementation details.