# Methods

This is a bridge reference. Use it when a method-level element issue reveals unclear method ownership, purity, side effects, or call-site semantics.

## Bridge Signals

- A method name or property reads as a query but mutates state, performs I/O, publishes events, writes cache, starts work, or releases resources.
- Method parameters include boolean traps, vague modes, weak bags, or nullish defaults that change behavior invisibly at call sites.
- A method updates object state and external resources in an order that can leave partial state.
- A method catches broad errors and converts unrelated failures into one default value.
- A method belongs to an object only by convenience and does not protect object state, invariant, lifecycle, collaborator, or protocol role.

## Handoff

- Route method placement, signature, object ownership, side-effect getter/setter questions, and public API decisions to `implementation-structure-design`.
- Route method readability and main-flow shape to `code-clarity-maintainability`.
- Route behavior-preserving method movement or extraction to `refactoring`.

