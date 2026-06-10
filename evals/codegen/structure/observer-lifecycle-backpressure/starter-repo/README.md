# Starter Repo

## Stack

Node.js order service with event publisher and Jest-style behavior tests.

## Initial State

`orders/orderService.ts` commits orders and emits an order-created event. A
proposed observer list calls notification, audit, and search indexing handlers
inside the transaction without bounds or cleanup.

## Files

- `orders/orderService.ts`
- `orders/orderEvents.ts`
- `orders/subscribers/notification.ts`
- `orders/subscribers/audit.ts`
- `orders/subscribers/searchIndex.ts`
- `tests/orders/orderEvents.test.ts`

## Constraints

The benchmark rejects unbounded observers, missing unsubscribe, transaction
breakage from subscriber exceptions, and missing subscriber observability.
