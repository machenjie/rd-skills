# Starter Repo

## Stack

TypeScript backend service with order, customer, billing, and shared utility
modules. Tests use a small unit test harness with in-memory fixtures.

## Initial State

The order API needs a new display-name field. Existing formatter helpers
already live near order and customer ownership, but there is also a tempting
generic utility module that should not receive order business logic.

## Files

- `src/orders/orderFormatter.ts` owns existing order formatting behavior.
- `src/customers/customerFormatter.ts` owns customer display labels.
- `src/orders/orderService.ts` exposes the public order read API.
- `src/orders/__tests__/orderService.test.ts` covers current reads.
- `src/shared/stringUtils.ts` contains only pure technical string utilities.

## Constraints

Do not add order terminology to shared utilities. Tests should call the public
order service or API boundary and should not assert private helper invocation.