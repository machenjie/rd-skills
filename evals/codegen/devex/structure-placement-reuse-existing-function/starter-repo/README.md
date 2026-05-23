# Starter Repo

## Stack

TypeScript service module with identity, tenant, invitation, and billing
packages. Tests use a lightweight unit test runner with in-memory repositories.

## Initial State

The invitation service compares raw email input and does not normalize before
lookup. Existing helpers already normalize email in `identity/email.ts`, validate
tenant access in `tenant/accessPolicy.ts`, and format billing amounts in
`billing/money.ts`.

## Files

- `src/identity/email.ts` exports `normalizeEmail()`.
- `src/tenant/accessPolicy.ts` exports `validateTenantAccess()`.
- `src/invitations/invitationService.ts` owns invitation lookup and send flow.
- `src/invitations/__tests__/invitationService.test.ts` covers current happy path.
- `src/billing/money.ts` exports unrelated `formatMoney()`.

## Constraints

Do not create `shared/utils` or move business rules out of owner modules. Tests
should verify invitation behavior through service APIs and not through private
helper implementation details.
