# Functions

This is a bridge reference. Use it only when a low-level element issue exposes a function-level concern, then route ownership to `implementation-structure-design`, `code-clarity-maintainability`, or `refactoring`.

## Bridge Signals

- Boolean trap parameters, weak bags, vague modes, or overloaded optional parameters make call-site behavior unclear.
- A local variable or expression problem repeats because the function mixes validation, mapping, decision, mutation, I/O, cleanup, and fallback.
- Function return values conflate missing, empty, denied, partial, retryable, terminal, and error states.
- A function name reads as pure but contains side effects, event publication, logging required for audit, time/randomness, cache mutation, or external I/O.

## Handoff

- Route signature, naming, placement, visibility, and public/private API decisions to `implementation-structure-design`.
- Route broad readability and main-flow decomposition to `code-clarity-maintainability`.
- Route behavior-preserving extraction, inline, or split work to `refactoring`.
- Keep this capability focused on the triggering variables, expressions, and statements.

