# Benchmark Prompt

## Task

Fix an object method that holds a lock while it calls a database or network
dependency.

## Context

The starter repository has an account updater that acquires an in-process lock,
mutates local state, calls a repository or external service while still holding
the lock, and then emits a notification. Under concurrency, throughput drops
and deadlock risk is unclear.

## Requirements

- Name the invariant protected by the lock.
- Shrink the critical section so no lock is held across network or storage IO.
- Use optimistic update, transaction boundary, queue, or outbox pattern when
  needed to preserve the invariant.
- Add timeout, deadlock, race, and contention analysis.
- Add stress, race-detector, or lock-contention evidence.

## Constraints

- Do not hold a lock across network or storage IO.
- Do not omit timeout behavior.
- Do not skip deadlock analysis.
- Do not rely only on serial unit tests.

## Deliverables

- Updated locking and IO boundary.
- Concurrency design and Performance-Aware Structure Decision.
- Stress, race, or contention evidence.

## Completion Evidence

- Review evidence shows the lock scope before and after.
- Tests or measurement show concurrent behavior is exercised.
- Deadlock and timeout behavior are documented.
