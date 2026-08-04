# Python Runtime Boundary Traps

This reference isolates Python import, async, resource, typing, mutability, serialization, and exception failure boundaries that need task-specific judgment.

## Decision Matrix

| Python facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Import and initialization | Side effects, ordering, reload, fork/spawn, explicit immutable environment or configuration inputs, registration owner, and failure behavior | Importing a module changes external state or works under the inspected entrypoint but fails under another |
| Async boundary | Blocking calls, task owner, exception observation, timeout, cancellation, context propagation, and shutdown | Work outlives its request or blocks the event loop without a bounded bridge |
| Iterator and resource lifetime | Acquisition owner, context or `finally` cleanup, early iterator exit, cancellation, and close errors | A generator, response, cursor, temporary resource, or lock survives an abandoned path |
| Type and runtime boundary | Parser owner, missing versus `None`, coercion, subclass/value quirks, and accepted or rejected shapes | Annotation, cast, or suppression is treated as runtime validation |
| Mutability and process model | Default objects, aliasing, shallow copies, caches, globals, worker model, and reset or synchronization | State silently crosses calls, tasks, tests, workers, or fork boundaries |
| Serialization | Format and version, admitted types, unknown fields, hooks, numeric/time semantics, and trust boundary | Round-trip success hides code execution, version skew, or representation loss |
| Exception boundary | Failure classes, cause chain, cleanup, partial state, transaction outcome, retry meaning, and caller contract | A broad handler converts distinct failures into success, retry, or an unactionable message |

## Decision Limits

- Repository conventions select mechanisms; prior task evidence may identify a fragile boundary, while current source and post-edit checks determine whether the selected claim remains supportable.
- Type-checker results apply to the configured program and accepted suppressions; they do not establish runtime input or serialization safety.
- An async test establishes the exercised schedule and cancellation point, not arbitrary scheduler interleavings or hidden library behavior.
- Import, fork/spawn, and reload behavior depends on actual process entrypoints and deployment configuration.
- Schema and public payload compatibility belong to the contract owner even when Python objects implement the local representation.
- A cleanup test covers named acquisition and exit paths; early iterator termination, cancellation, process exit, and native handles remain separate risks.
