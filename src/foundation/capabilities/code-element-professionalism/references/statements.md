# Statements

## Purpose

Use this reference when a statement's control flow, loop behavior, cleanup, error boundary, transaction order, side-effect order, concurrency, or async lifecycle can affect correctness, data integrity, reliability, or reviewability.

Statements own observable ordering. A sequence that looks locally plausible can still be wrong if it hides main flow, swallows errors, leaks resources, publishes events before durable state, or launches work without cancellation and ownership.

## Decision Scope

Review statements that govern validation, policy, mutation, persistence, cache, events, notifications, external I/O, file/process/socket/resource lifecycle, locks, async tasks, transactions, returns, throws, panics, and error translation.

Keep main flow visible. Use guard clauses when they reduce nesting without hiding side effects. Use switch or match when it improves constant-choice or exhaustive-case clarity.

## If, Guard, Switch, and Match

Branches should make the primary path and exceptional paths visible. Guard clauses are useful when they stop invalid work early and do not bury cleanup, audit, event, or transaction behavior.

Switch and match statements are appropriate when they improve constant-choice clarity, exhaustive coverage, or state transition review. Fallthrough must be explicit and rare. If fallthrough is required, it needs a local language marker, comment, or test that proves the shared behavior is intentional.

Empty branches are findings until they are removed or made visibly intentional by local convention.

## Loop Selection and Loop State

Prefer range or iterator loops when they express element traversal and do not hide required index semantics. Use raw index loops only when index, cursor, window, offset, mutation, or ordering semantics matter.

Do not mutate raw loop control variables inside the body unless invariant and termination are obvious or documented. Loop counters, cursors, collection mutation, and retry budgets need one owner and one termination story.

Loops that wait, poll, retry, batch, page, stream, or fan out require timeout, backoff, cancellation, and resource behavior when material.

## Break, Continue, Fallthrough, and Empty Statements

Make empty statements visible or remove them. Empty loops, empty branches, ignored returns, and no-op catches should not pass as professional code merely because they compile.

`break` and `continue` should not skip required cleanup, audit, metrics, transaction rollback, lock release, or response construction. If they do, restructure the statement or use the language's cleanup construct.

Fallthrough must be explicit and rare. Accidental fallthrough is a correctness defect; intentional fallthrough is a contract.

## Try, Catch, Except, Finally, Defer, With, Using, and RAII

Avoid broad `try`/`catch`/`except`; catch only the operation whose failure is being handled. A broad try scope can convert unrelated failures into the wrong response, hide partial writes, or swallow programmer errors.

Cleanup must cover success, error, early return, cancellation, and timeout paths. Use language idioms: RAII, `defer`, context managers, try-with-resources, `using`, `finally`, or explicit close/unsubscribe.

Error handling must preserve the boundary contract. Do not catch and continue unless the failure is expected, scoped, and tested.

## Return, Throw, Panic, and Error Boundary Statements

Return, throw, panic, raise, reject, and error-boundary statements must preserve boundary semantics and must not swallow material errors.

A return should not bypass required cleanup or source-of-truth consistency. A thrown error should keep enough category/context for the caller to respond correctly without leaking secrets or raw user input.

Panic/fatal paths require a language/runtime owner and are not a substitute for ordinary error handling in recoverable product flows.

## Transaction and Side-Effect Ordering

Validation, policy, mutation, persistence, event/cache/external I/O, and response order must be visible.

Events, notifications, cache writes, and external I/O should occur after source-of-truth commit unless a stronger capability approves the exception. If the exception is intentional, route to `data-side-effect-flow-tracing`, `transaction-consistency`, idempotency, integration, or reliability ownership.

Do not publish, cache, notify, or call an external system based on state that can still roll back unless the compensation or outbox pattern is explicit and tested.

## Concurrency, Cancellation, Lock, and Async Statements

Lock scope must not cross blocking I/O unless explicitly justified and tested. Statements that spawn async tasks, goroutines, threads, timers, subscriptions, workers, or callbacks require owner, cancellation, timeout, backpressure, and error propagation decisions when material.

Detached work is not free. The caller, service, runtime, or lifecycle owner must know who observes completion, handles failure, cancels on shutdown, and releases resources.

When concurrency is a language-runtime concern, hand off to the language and reliability capabilities rather than treating it as only a local statement style issue.

## Statement Ordering and Main-Flow Visibility

Keep the main flow visible by separating validation, policy decisions, mutation, persistence, side effects, cleanup, and response construction. Avoid statement sequences where a reviewer must reconstruct the state machine from interleaved branches and side effects.

Side-effect statements should read like side effects. Hidden writes in mappers, getters, predicates, serializers, comprehensions, debug hooks, or display code should be routed to side-effect flow and structure review.

## Language Handoff

Hand off when statement behavior depends on:

- JavaScript or TypeScript async/await, promise rejection, `finally`, render lifecycle cleanup, switch fallthrough, event-loop blocking, or abort signals.
- Python context managers, broad `except`, `finally`, generator cleanup, async tasks, cancellation, or mutable iteration.
- Go `defer`, `panic`/`recover`, goroutines, channel close, context cancellation, error shadowing, or loop variable capture.
- Java or JVM try-with-resources, checked exceptions, synchronized blocks, thread pools, transactions, or stream lifecycle.
- Rust `match`, `?`, drop order, RAII guards, async cancellation, panics, mutex guards, or ownership moves.
- C or C++ RAII, switch fallthrough, goto cleanup, destructor order, locks, atomics, exceptions, or resource handles.

## Fix Patterns

- Replace deep nesting with guard clauses when cleanup and side effects remain visible.
- Use switch or match for constant choices or exhaustive states when it improves reviewability.
- Replace raw index loops with iterator/range loops unless index/cursor/window semantics matter.
- Move loop counter/cursor mutation into one visible owner.
- Remove empty statements or add explicit language-conventional markers for intentional no-op behavior.
- Narrow try/catch/except scope to the operation being handled.
- Add RAII, `defer`, context manager, try-with-resources, `using`, `finally`, close, unsubscribe, or rollback coverage.
- Return or throw with boundary-appropriate error categories; do not swallow material errors.
- Reorder transaction, event, cache, notification, and external I/O statements so source-of-truth commit happens first.
- Add cancellation, timeout, backpressure, and error propagation for spawned work when material.

## Failure Modes

- Main flow is hidden behind nested branches and interleaved side effects.
- A guard clause skips cleanup or audit work.
- Switch fallthrough is accidental or untested.
- A raw loop mutates its counter or collection from multiple places.
- Empty loops, branches, no-op catches, or ignored returns hide behavior.
- A broad catch converts unrelated failures into the same result.
- Cleanup misses error, early return, cancellation, or timeout paths.
- A return, throw, or panic swallows a material error or changes boundary semantics.
- Event, cache, notification, or external I/O occurs before commit.
- A lock is held across blocking I/O.
- An async task, goroutine, thread, timer, or subscription has no owner, cancellation, timeout, backpressure, or error propagation.

## Review Questions

- Is the main flow visible without reconstructing hidden side effects?
- Does each branch, loop, break, continue, fallthrough, return, throw, and cleanup path preserve required ordering?
- Is the try/catch/except scope no broader than the handled operation?
- Are resources released on success, error, early return, cancellation, and timeout?
- Do events, cache writes, notifications, and external I/O happen after source-of-truth commit?
- Does any concurrency or async statement need owner, cancellation, timeout, backpressure, or error propagation evidence?
- Should the remaining issue be owned by language, side-effect, transaction, reliability, integration, or security capabilities?

## Evidence

- Tests cover loop termination, empty inputs, fallthrough branches, cleanup on error, early return, cancellation, and timeout when material.
- Transaction tests prove no event, cache write, notification, or external I/O occurs when commit fails, and that side effects happen after successful commit.
- Concurrency or async tests prove cancellation, timeout, error propagation, and lock-scope expectations when material.
- Review artifacts identify statement ordering, cleanup owner, external side effects, language handoff, and residual risk.
