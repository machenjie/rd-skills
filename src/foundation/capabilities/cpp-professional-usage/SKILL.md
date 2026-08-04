---
name: cpp-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when C/C++ changes cross ownership, UB, ABI/FFI, exception, concurrency, or target-build boundaries; skip tool-only work."
---

# cpp-professional-usage

## Registry Trigger

**Use when**

- C or C++ code changes resource ownership, borrowed lifetime, undefined behavior exposure, ABI/FFI, exception flow, concurrency, or target-specific build behavior.
- Native correctness depends on compiler, optimizer, architecture, foreign runtime, or cleanup invariants in the current scope.

**Do not use when**

- The open decision is language/runtime selection, package policy, build-tool mechanics, test strategy, or a measured performance bottleneck.
- No C/C++ source, native boundary, public header, generated binding, or target behavior changes.

## Skill Role

Protect C/C++ resource and object lifetimes, undefined-behavior boundaries, exception cleanup, concurrency publication, ABI/FFI representation, and target-dependent semantics.

## High-Value Rules

- Bind deterministic resource acquisition and release to a scoped owner; make external-ABI transfer explicit.
- Define validity for pointers, references, views, iterators, callbacks, and moved-from objects across invalidation events.
- Prove lifetime, bounds, overflow, initialization, aliasing, alignment, representation, and race safety beyond compilation.
- Define exception or status boundaries, unwind cleanup, destructor failure, and caller translation.
- Fix ABI layout, calling convention, symbols, allocators, buffers, errors, callbacks, threads, and binding authority.
- State happens-before, publication, synchronization ownership, cancellation cleanup, and object lifetime.
- Define language standard, compiler flags, visibility, platform assumptions, and generated artifacts for explicit targets.
- Return the C/C++ safety decision with inspected native evidence, proof limits, and specialist routes even when no Reference loads.

## Anti-Patterns

- `shared_ptr`, a raw handle, or a custom deleter is introduced because ownership remains undecided.
- A view, iterator, callback capture, or foreign buffer escapes the storage or thread lifetime that makes it valid.
- A local build, one sanitizer lane, or one compiler is generalized to unsupported optimizer, architecture, or platform combinations.
- Source compatibility or unit-test success is presented as binary compatibility for exported layout, symbols, exceptions, or allocators.

## Stop Conditions

- Route language, package, build, test, and performance decisions to their specialist owners.
- Route synchronization protocols to `concurrency-control`.
- Route kernel, driver, allocator, interrupt, lock-free, hardware, or deep ABI/FFI design to `low-level-systems-extension`.

## Output Contract

- C C++ safety decision with ownership lifetime undefined behavior exception concurrency ABI FFI target-build risks and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [native safety evidence](references/native-safety-evidence.md) | evidence-pattern | Native change crosses ownership borrowed lifetime undefined behavior concurrency ABI FFI or target-build boundary needing failure-specific proof | Current native ownership contracts and target-specific checks settle the changed boundary | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
