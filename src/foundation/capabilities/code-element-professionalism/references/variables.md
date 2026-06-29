# Variables

## Purpose

Use this reference when a variable's initialization, scope, lifetime, mutability, shadowing, reuse, capture, or default semantics can affect correctness, reviewability, security, resource ownership, transaction behavior, or test isolation.

Variables are not just names for storage. They are local contracts about what value exists, when it becomes meaningful, who may change it, which states it can represent, and how long another caller, closure, task, thread, or test may observe it.

## Decision Scope

Review variables that participate in behavior, permission decisions, resource cleanup, transaction state, cache/event/external I/O ordering, request or tenant context, concurrency, returned values, loop/cursor state, and generated code.

Keep this capability local. If the variable problem exposes a bad function signature, boolean trap, misplaced constant, shared utility, object owner, or file/module boundary, record the bridge and hand off to `implementation-structure-design`. If correctness depends on language lifetime, ownership, pointer/reference, async capture, or nullability semantics, hand off to `language-idiom-enforcement` and the relevant language capability.

## Definition Timing

Introduce variables at the smallest readable scope where their initializer is available and meaningful. Do not introduce variables before they have meaningful initializer values unless a language or framework input API forces an early declaration.

Early declarations are acceptable only when the lifecycle is explicit: a later assignment is guaranteed before all reads, the uninitialized state cannot leak to another branch, and the handoff names why the language or API requires the shape.

Avoid read-before-write on any branch, exception path, early return, loop path, cancellation path, or retry path. A variable initialized only in a happy path is unsafe when error handling, logging, cleanup, or response construction reads it later.

## Initialization

Initializers should express the variable's first valid value. Prefer direct initialization over placeholder assignment followed by mutation. When construction can fail, keep the partially constructed state private to the branch or operation that owns it.

Do not use sentinel or uninitialized values to avoid real initialization unless the sentinel has explicit domain meaning and tests. A placeholder used only to satisfy control flow is a sign that the branch, return shape, or error boundary needs redesign.

For nullable, optional, pointer, reference, or dynamic values, state whether the variable can be absent, whether absence is expected, and where absence is converted to a user-visible, API, or domain state.

## Default and Sentinel Semantics

Distinguish missing, empty, false, zero, unknown, denied, expired, partial, and error states when those states mean different things. Do not collapse them into one `null`, `None`, `nil`, empty string, empty collection, false, zero, default enum, or "not found" value unless the domain contract explicitly says they are equivalent.

Sentinels must have an owner and a test. If a sentinel represents "not loaded yet", "permission denied", "not found", "expired", "partial result", or "upstream error", name that state rather than letting a generic missing value carry it.

Default values at input boundaries require extra care. A default for convenience can become a policy decision if it changes authorization, pricing, retention, retry count, timeout, pagination, localization, or feature behavior.

## Scope and Shadowing

Narrow scope until each variable has one reader set, one reason to change, and no accidental lifetime. A variable needed only inside one branch, loop, transaction, cleanup block, or test fixture should usually live there.

Avoid shadowing when it affects errors, permissions, transactions, resources, tenant/request context, loop counters, or state variables. Shadowing may be idiomatic for small immutable values in some languages, but it must not hide which error, transaction, context, or resource is being checked, closed, committed, rolled back, or returned.

When shadowing is kept, reviewers need language-convention evidence and proof that the outer value is not used after the shadowed scope in a way that depends on the inner assignment.

## Mutability and Ownership

Use immutable, const, final, readonly, or single-assignment values by default when mutation is not required. Mutable variables need a mutation owner and reason.

Record what can mutate the value: the current block, a loop, a callback, an async task, a closure, a thread, a test fixture, or another object through an alias. A mutable variable with no clear owner is hidden shared state even when it is local.

Mutation is acceptable when it models one concept through time, such as an accumulator, cursor, transaction status, retry budget, or builder. It is not acceptable when the same variable is reused for unrelated concepts or lifecycle phases.

## Concept Identity and Variable Reuse

Do not reuse one variable for unrelated concepts or lifecycle phases. Names must express current value semantics, not merely origin or type noise.

Bad reuse examples include an ID variable later holding a loaded object, a request variable later holding a response, a permission result later holding an error, or a transaction variable later holding a committed boolean. Introduce a new variable or smaller scope when the concept changes.

If a variable intentionally changes phase, such as `pending_items` becoming `processed_items`, prefer separate names or a small value object/result structure so the phase transition is visible and testable.

## Naming and Searchability

Names should carry the value's role, state, and domain meaning. Avoid names that only repeat type, source, or implementation detail, such as `data`, `result`, `item`, `obj`, `tmp`, or `response`, when the value participates in a material decision.

Searchability matters for reviews and same-pattern scans. Names for permission, tenant, transaction, resource, cache, event, retry, cancellation, and cleanup state should be specific enough that a maintainer can find related code and tests.

Do not encode stale origin into a name after transformation. A value read from a request but validated into a domain decision should be named for the decision, not only for the request field it came from.

## Lifetime, Aliasing, and Capture

Captured variables in closures, callbacks, async tasks, goroutines, threads, comprehensions, and event handlers require lifetime, stale-value, and race review. Confirm whether the captured value is evaluated now, evaluated later, copied, borrowed, referenced, or shared.

Aliases can make local variables non-local. Returned mutable collections, passed-in buffers, shared contexts, transaction objects, and resource handles may outlive the local block. State whether callers can mutate them and whether tests isolate that mutation.

Loop captures are a common failure point. Each scheduled callback, goroutine, promise, or lambda should capture the intended per-iteration value rather than a shared loop variable unless the language makes capture-by-value explicit.

## Global or Module-Level Mutable State

Global or module-level mutable state requires lifecycle, synchronization, reset, and test isolation evidence. It must have a construction owner, shutdown/reset owner, concurrency policy, and clear behavior across tests, workers, hot reload, and retries.

Do not use module-level mutable defaults, caches, registries, or accumulators to avoid passing data explicitly unless a stronger capability owns the lifecycle and synchronization decision.

When global state is necessary, tests must prove reset/isolation behavior and reviewers must check that secrets, user data, tenant context, request context, and transaction handles do not leak across calls.

## Language Handoff

Hand off to language-specific capabilities when correctness depends on:

- JavaScript or TypeScript `var`/`let`/`const`, closure capture, `undefined` versus `null`, optional properties, or readonly typing.
- Python `None`, mutable defaults, late binding closures, comprehensions, dataclass defaults, or object aliasing.
- Go short declaration shadowing, `err` handling, goroutine capture, zero values, pointers, and deferred cleanup.
- Java or JVM finality, nullable annotations, object references, thread visibility, and try-with-resources.
- Rust ownership, borrowing, lifetimes, `Option`, `Result`, mutation, and interior mutability.
- C or C++ initialization, object lifetime, references, pointers, move semantics, RAII, and undefined behavior.

## Fix Patterns

- Move the declaration into the smallest block that has the real initializer.
- Split branches so a variable cannot be read before it is assigned.
- Replace placeholder values with explicit result, optional, enum, or error states.
- Replace concept reuse with a new name or a narrower scope.
- Use immutable binding by default and document the owner of required mutation.
- Rename or remove shadowing around errors, resources, transactions, permissions, tenant context, or loop counters.
- Capture per-iteration values explicitly for callbacks, async tasks, threads, and event handlers.
- Copy or freeze returned collections when callers must not mutate local state.
- Add reset fixtures for module-level mutable state or move state behind an owned lifecycle boundary.

## Failure Modes

- A branch reads a variable initialized only on another branch.
- Exception or cleanup code logs, returns, commits, or closes a value that may not exist.
- `null`, `None`, false, zero, empty string, empty collection, or default enum silently merges distinct domain states.
- A local variable shadows an outer error, transaction, permission, tenant, context, resource, or loop variable.
- One variable changes from ID to object to response to error across a function.
- A closure captures stale loop state, request context, transaction handle, or mutable collection.
- A returned alias lets callers mutate internal state after validation.
- Global mutable state leaks across tests, requests, users, tenants, workers, or retries.

## Review Questions

- Where is the first meaningful assignment, and can every read prove it already happened?
- Does the name describe the current value semantics for the whole lifetime?
- Are missing, empty, false, zero, unknown, denied, expired, partial, and error states distinct where the domain needs them to be?
- Who owns mutation, and why is immutability insufficient?
- Is shadowing harmless by language convention, or does it hide a material value?
- Can any closure, callback, async task, thread, comprehension, or event handler observe a stale or racing value?
- Does any alias or global/module state outlive the local operation?

## Evidence

- Tests cover missing, empty, false, zero, unknown, denied, expired, partial, and error states when those states differ.
- Regression tests prove no read-before-write, unsafe shadowing, mutable default, or concept reuse remains in the repaired path.
- Static analysis, compiler warnings, typecheck, linter, or review artifacts cover initialization, mutability, shadowing, capture, and aliasing where available.
- Handoff states any language-specific lifetime, ownership, or concurrency behavior routed to another capability.
