# Variables

Use this reference when initialization, scope, mutability, shadowing, reuse, lifetime, or sentinel semantics can affect behavior.

## Decision Checks

- Identify the first assignment, all reads, all writes, and every branch that can skip initialization.
- Confirm the variable name describes one concept for its full lifetime.
- Narrow scope when a value is only needed inside one branch, loop, transaction, or cleanup block.
- Distinguish reassignment that updates one concept from reuse that changes meaning.
- Treat shadowing as a risk for errors, permissions, resources, transactions, loop counters, tenant IDs, request context, and state machines.
- State whether the variable is immutable by design, mutable by necessity, or mutable only because the language lacks a cheaper local construct.
- Define sentinel/default semantics for `null`, `None`, zero, false, empty string, empty collection, default enum, missing field, and unknown value.
- Inspect closure capture and loop variable capture when asynchronous callbacks, goroutines, promises, lambdas, comprehensions, or event handlers are involved.

## Fix Patterns

- Initialize before the branch, or split the branch so reads cannot happen before writes.
- Replace concept reuse with a new variable name or smaller block scope.
- Replace sentinel values with explicit result types, optionals, enums, or named states when the language/project supports them.
- Move loop state inside the smallest valid loop or iterator owner.
- Rename shadowed variables or split inner scopes when shadowing affects reviewability.

## Evidence

- Tests cover missing, empty, false, zero, unknown, denied, expired, partial, and error states when those states differ.
- Static analysis, typecheck, compiler warning, linter, or review evidence proves no read-before-write or unsafe shadowing remains.
- Handoff states any language-specific lifetime or ownership behavior routed to another capability.

