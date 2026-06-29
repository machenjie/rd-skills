# Statements

Use this reference when loops, branches, switches, try/catch/finally/defer, cleanup, ignored returns, transaction order, or local side-effect visibility can affect behavior.

## Decision Checks

- Confirm each loop has one clear iteration owner, termination condition, cursor/counter mutation location, and collection-mutation rule.
- Treat empty loops, empty branches, no-op catches, ignored return values, and intentional fallthrough as review findings until made explicit.
- Confirm switch/case or pattern-match fallthrough is supported by the language and intentional in the repository's convention.
- Keep try/catch/finally/defer scope narrow enough that unrelated failures are not converted into the same result.
- Release resources on success, failure, early return, cancellation, and timeout paths.
- Keep commits, cache writes, events, notifications, external I/O, and irreversible side effects in an order that matches source-of-truth consistency.
- Do not hide writes, cache mutation, event emission, time, randomness, logging, or metrics inside statements that read as pure checks.

## Fix Patterns

- Split a loop into explicit phases when counter/cursor mutation is not locally obvious.
- Add an explicit fallthrough marker or separate case body according to language convention.
- Move unrelated operations outside a try block and catch only the failure being handled.
- Use `finally`, `defer`, RAII, context managers, or explicit close/unsubscribe calls according to language convention.
- Reorder side effects so durable state commits before downstream publication unless a stronger capability approves the exception.

## Evidence

- Tests cover loop termination, empty inputs, fallthrough branches, cleanup on error, and transaction/event ordering when material.
- Review artifacts identify statement ordering, cleanup owner, and any external side effects.
- Handoff routes cross-boundary side effects, retries, idempotency, or transaction consistency to the owning capability.

