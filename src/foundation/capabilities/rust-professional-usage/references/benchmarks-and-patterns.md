# Rust Safety Boundary Traps

This reference isolates Rust ownership, unsafe, panic, cancellation, Send/Sync, and FFI boundaries where compiler checks leave task-specific obligations.

## Decision Matrix

| Rust facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Ownership and borrowing | Owner, mutation authority, borrow duration, invalidation, clone cost, drop order, and callback capture | Clone or shared ownership hides who may mutate or end the value |
| Movement and pinning | Address stability, self-reference, projection, replacement, drop guarantee, and unsafe caller obligations | A pinned or self-referential value is moved through an apparently safe path |
| Unsafe memory | Aliasing, provenance, alignment, initialization, layout, bounds, lifetime, and safe-wrapper preconditions | The comment describes the operation but omits the invariant that makes it sound |
| Panic and destruction | Recoverable error contract, unwind or abort policy, destructor behavior, thread/task observation, and FFI translation | Panic crosses a boundary that cannot preserve cleanup or caller semantics |
| Async and cancellation | Await cancellation points, partial state, resource cleanup, task owner, blocking work, timeout, and shutdown | Dropped or detached work leaves a half-transition or hidden failure |
| `Send` and `Sync` | Captured fields, interior mutability, callback thread, guard lifetime, unsafe impl invariant, and executor requirements | A wrapper is marked thread-safe while an inner value or callback violates the promise |
| FFI | Representation, allocator, buffers and strings, error channel, callback lifetime, thread affinity, generated binding, and unwind rule | Rust and foreign code disagree about layout, ownership, or who may call back when |

## Decision Limits

- Repository toolchain and runtime choices select mechanisms; this reference does not prescribe an async runtime, error crate, synchronization primitive, or FFI generator.
- Typed errors matter where callers branch on failure; context-rich erased errors can remain appropriate at orchestration boundaries.
- Compiler acceptance establishes the checked Rust program, not foreign-code behavior, unsafe soundness, cancellation safety, or semver compatibility.
- Miri, sanitizers, fuzzing, and concurrency exploration cover their selected target, inputs, and schedule model; skipped lanes retain an owner and risk.
- Safe Rust around an unsafe dependency inherits the dependency's documented and undocumented contracts.
- Final handoff claims cite current source and relevant post-edit checks; otherwise record the unrun validation and its residual risk.
