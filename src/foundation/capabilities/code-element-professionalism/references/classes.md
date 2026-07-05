# Classes

This is a bridge reference. Use it only when a code element exposes class responsibility, state, invariant, or lifecycle risk.

## Bridge Signals

- A class field is defaulted, shadowed, or reused across lifecycle phases without explicit invariant semantics.
- A constructor leaves fields uninitialized or relies on sentinel values that callers cannot distinguish.
- A property or getter mutates state, performs I/O, starts timers/subscriptions, or changes lifecycle.
- Class methods share mutable state through broad fields instead of narrow local variables or value objects.
- A class is created only to hold constants, flags, or procedural helpers that do not protect state or invariants.

## Handoff

- Route object responsibility, class creation, field ownership, inheritance, lifecycle, and collaborator decisions to `implementation-structure-design`.
- Route readability problems from oversized or mixed class flow to `code-clarity-maintainability`.
- Route behavior-preserving class extraction, collapse, or movement to `refactoring`.

