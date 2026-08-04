---
name: low-level-systems-extension
description: "For analysis/task/review agents using a Professional Skill on kernels, drivers, ABI/FFI, memory, concurrency, or syscalls; not for work without a native boundary."
---

# low-level-systems-extension

## Role

Consult this focused Layer 3 Domain Skill at native and operating-system
boundaries. Provide `analysis-agent`, `task-agent`, and `review-agent` with
memory, concurrency, ABI/FFI, syscall, unsafe-code, and profiling constraints at
native and operating-system boundaries.

## When To Use

- kernel, driver, native memory, ABI/FFI, real-time behavior, syscall, or systems concurrency

## Do Not Use

- managed-runtime application work with no native or operating-system boundary
- C++ or Rust usage without a native ABI, OS, or resource boundary

## Required Inputs

- ownership, lifetime, callers, ABI, platform, privilege, concurrency, and timing boundaries
- compiler and runtime versions, deployed consumers, threat model, and representative measurements

## Professional Decision Rules

- **Prove ownership and lifetime**: trace acquisition, transfer, borrowing, publication, and release across functions, threads, languages, callbacks, and failure paths.
- **Maintain unsafe contracts**: state preconditions, aliasing and lifetime assumptions, caller duties, containment, and negative tests for every unsafe boundary.
- **Build a scoped deadlock-freedom argument**: derive an acyclic lock order across reachable acquisition, reentrancy, callback, cancellation, cleanup, and teardown paths.
- **Disclose deadlock proof limits**: treat runtime evidence as corroboration and name untested schedules and residual deadlock risk.
- **Bound undefined-behavior claims**: enumerate the affected memory and concurrency invariants, supported compiler/target/build matrix, analyzed paths, and targeted static and dynamic evidence. Claim absence only where the method is sound and its assumptions and state space are stated; list unproved inputs, schedules, platforms, and foreign behavior.
- **Protect deployed ABI consumers**: prove compatibility or coordinated replacement for layout, calling convention, symbols, allocator, and ownership changes.
- **Constrain privileged capability**: select containment from the target OS, reachable syscalls, authority, recovery path, and threat model.
- **Bound sensitive arithmetic**: prove overflow, truncation, signedness, and size conversions before allocation, indexing, parsing, or I/O.
- **Measure optimization causality**: use representative profiles and compare treatment against correctness, resource, and tail-latency constraints.

## High-Value Gotchas

- FFI callback publication loses ownership or lifetime
- cancellation cleanup introduces a rare lock cycle
- an unchanged signature changes allocator ownership
- signed-overflow assumptions remove a bounds check
- recovery uses a syscall absent from containment tests

## Execution Checklist

1. Trace ownership, callers, concurrency, privilege, and compatibility at the affected boundary.
2. Select mechanisms from platform, compiler behavior, threat model, and measurements.
3. Prove memory, race, ABI, fault, and recovery behavior within stated limits.

## Stop / Escalation Conditions

- Stop when ownership, ABI consumers, concurrency topology, target platform, or privilege boundary cannot be verified.
- Escalate exploitable memory behavior, kernel/driver impact, real-time deadline risk, and incompatible deployed consumers.

## Output Contract

- State the systems invariant, risk condition, selected mechanism, safety and compatibility argument, representative performance evidence, current post-edit validation obligations and result, proof limits, unverified inputs/schedules/platforms/foreign behavior, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | native memory ABI FFI syscall concurrency or platform-resource behavior needs domain risk closure | C++ or Rust is mentioned without a native ABI OS or resource boundary | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
