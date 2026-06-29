# Files

This is a bridge reference. Use it when file-scope variables, constants, statements, or initialization order create local hazards.

## Bridge Signals

- File-scope mutable state, caches, singletons, or default config values affect tests, tenants, requests, or concurrent calls.
- Constants are placed far from the owner or promoted to public scope without a real owner boundary.
- Import-time statements perform I/O, read environment, start timers, register handlers, or mutate global state.
- A file hides cleanup, event ordering, or transaction logic behind local helper names.

## Handoff

- Route file ownership, file split/merge, public exports, and placement to `implementation-structure-design`.
- Route broad navigation and main-flow readability to `code-clarity-maintainability`.
- Route behavior-preserving file movement to `refactoring`.
- Keep local review focused on file-scope variables, expressions, and statements that cause the signal.

