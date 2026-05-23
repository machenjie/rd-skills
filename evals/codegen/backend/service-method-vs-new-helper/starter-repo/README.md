# Starter Repo

## Stack

TypeScript backend service with modular order, auth, and persistence layers.
Tests use service-level unit tests with in-memory repositories and fixed clocks.

## Initial State

`OrderService.cancelOrder()` performs authorization, starts the transaction,
loads the order, and delegates policy checks. `OrderPolicy` owns cancellation
eligibility but does not yet enforce the cancellation deadline.

## Files

- `src/orders/application/OrderService.ts` owns cancellation orchestration.
- `src/orders/domain/OrderPolicy.ts` owns order cancellation rules.
- `src/orders/domain/Order.ts` represents order state and deadline data.
- `src/orders/__tests__/OrderService.test.ts` covers successful cancellation.
- `src/shared/utils/date.ts` contains pure date math only.

## Constraints

Preserve transaction and authorization flow. Keep business rules in the order
module. Shared date utilities may contain only pure technical date arithmetic
with no order terminology.
