# Starter Repo

## Stack

TypeScript backend service with domain objects, application services,
repositories, and unit tests.

## Initial State

Order cancellation already flows through `OrderService`, which checks
authorization, opens a transaction, loads an order repository record, and emits
notifications. `Order` owns status transitions, while `OrderPolicy` owns
deadline rules. The current change needs a new cancellation eligibility rule.

## Files

- `src/orders/Order.ts` owns order state transitions.
- `src/orders/OrderPolicy.ts` owns deadline and eligibility business rules.
- `src/orders/OrderService.ts` coordinates cancellation use cases.
- `src/orders/OrderRepository.ts` persists order state.
- `src/orders/__tests__/OrderService.test.ts` covers cancellation behavior.

## Constraints

Do not create `shared/utils` for order business rules. Do not export new helpers
unless they are stable public contracts. Tests should exercise public order or
service behavior, not private helper calls.
