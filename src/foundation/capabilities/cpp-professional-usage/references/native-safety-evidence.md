# C And C++ Native Boundary Traps

This reference isolates C and C++ ownership, lifetime, undefined-behavior, concurrency, ABI/FFI, and target-build boundaries that ordinary compilation can miss.

## Decision Matrix

| Native facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Resource ownership | Acquisition, scoped owner, transfer, move/copy policy, deleter, early-return and exception cleanup, and foreign release API | Resource release depends on a caller convention that the type does not encode |
| Borrowed lifetime | Owner lifetime, invalidation, iterator/view/pointer escape, callback capture, thread handoff, and moved-from use | A non-owning handle survives reallocation, destruction, or deferred execution |
| Object and memory model | Bounds, initialization, provenance, aliasing, alignment, representation, overflow, and optimizer assumptions | Code works in one build while relying on undefined or implementation-defined behavior |
| Error and cleanup | Exception or status boundary, destructor behavior, partial construction, cleanup failure, translation, and FFI unwind rule | Error translation loses cleanup, ownership, or caller-visible failure meaning |
| Concurrency | Shared-state owner, publication, happens-before relation, atomic order, lock lifetime, cancellation, and destruction | An object becomes visible before its state or lifetime invariant is established |
| ABI and FFI | Layout, symbols, calling convention, allocator pair, buffers and strings, callback/thread rules, versioning, and generated authority | Producers and consumers compile while disagreeing on binary representation or ownership |
| Target build | Standard, compiler and flags, architecture, endian and alignment, visibility, target-scoped dependencies, and generated artifacts | Ambient flags, transitive includes, or one platform decide behavior accidentally |

## Decision Limits

- C interoperability can require raw handles; the boundary still names ownership transfer, release authority, lifetime, and failure behavior.
- Sanitizer lanes observe different defect classes and selected executions; a green lane does not establish safety for another target or schedule.
- Static analysis and warnings find configured patterns; suppressions retain scope, reason, and an accountable cleanup condition.
- Source compatibility, binary compatibility, and FFI compatibility are separate claims with separate consumers and evidence.
- Compiler, optimizer, standard-library, architecture, and build-mode changes can invalidate earlier native evidence.
- Current checks cover named targets and inputs; unrun sanitizer, fuzz, stress, ABI, or platform lanes remain explicit residual risks.
