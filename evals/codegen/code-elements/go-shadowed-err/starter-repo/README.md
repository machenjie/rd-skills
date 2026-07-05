# Starter Repo

## Stack

Go service code with transactional repository writes.

## Initial State

An inner `err :=` shadows an outer `err` checked after the transaction block.

## Files

- `service/orders.go`
- `service/orders_test.go`

## Constraints

Keep transaction boundaries stable and do not introduce wrappers.

