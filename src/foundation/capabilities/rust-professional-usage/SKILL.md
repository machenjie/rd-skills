---
name: rust-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Rust changes cross ownership, unsafe/FFI, panic, cancellation, or Send/Sync boundaries; skip tool-only work."
---

# rust-professional-usage

## Registry Trigger

**Use when**

- Rust code changes ownership or lifetime, unsafe or FFI, panic or error behavior, async cancellation, or `Send`/`Sync` boundaries.
- Compiler-enforced safety depends on a caller, runtime, foreign-code, or shutdown invariant in the current scope.

**Do not use when**

- The open decision is language/runtime selection, package policy, build mechanics, test strategy, or measured performance work.
- No Rust-specific ownership, unsafe, concurrency, panic, or foreign boundary changes.

## Skill Role

Protect Rust ownership and lifetimes, unsafe contracts, panic and cancellation behavior, `Send`/`Sync` obligations, and FFI representation and ownership.

## High-Value Rules

- Model ownership, borrowing, mutation, and invalidation before adding clones, reference counting, or interior mutability.
- Define unsafe aliasing, alignment, initialization, provenance, lifetime, and thread invariants behind the safe surface.
- Define typed recoverable errors while preventing unwinding across incompatible FFI boundaries.
- Keep partial state and resources safe when futures are dropped at await points.
- Give spawned and blocking work owned completion, failure observation, and shutdown while deriving `Send` and `Sync` through captured fields and callbacks.
- Define FFI representation, allocation, buffers, errors, callbacks, thread affinity, and unwind behavior.
- Do not rely on async cleanup from `Drop` or permit a second panic during unwinding.
- Return the Rust safety decision with inspected language evidence, proof limits, and specialist routes even when no Reference loads.

## Anti-Patterns

- Clone, `Arc`, `Mutex`, or interior mutability is added until the borrow checker accepts code while ownership remains unnamed.
- A narrow unsafe operation is wrapped by a safe API that accepts states its safety contract did not validate.
- Compile, lint, or one target-specific interpreter run is treated as proof for foreign callers, optimizer behavior, or supported architectures.
- Detached tasks, blocking work, guards across await, or cancellation leave a protocol transition or resource lifetime without an owner.

## Stop Conditions

- Route language, package, build, test, performance, and public compatibility decisions to their specialist owners.
- Route atomics and synchronization protocols to `concurrency-control`.
- Route ABI, operating-system, allocator, interrupt, or hardware invariants to `low-level-systems-extension`.

## Output Contract

- Rust safety decision with ownership lifetime unsafe panic cancellation Send Sync FFI risks proof limits and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Rust change crosses ownership unsafe panic cancellation Send Sync or FFI boundary whose soundness remains unclear | Current Rust ownership contracts and focused safety checks settle the changed boundary | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
