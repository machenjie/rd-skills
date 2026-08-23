---
name: low-level-systems-extension
description: "For analysis/task/review agents using a Professional Skill on kernels, drivers, ABI/FFI, memory, concurrency, or syscalls; not for work without a native boundary."
---

# low-level-systems-extension

## Role

Apply this focused Layer 3 Domain Skill at verified native or operating-system boundaries.
Provide `analysis-agent`, `task-agent`, and `review-agent` with memory, concurrency,
ABI/FFI, syscall, resource, and profiling constraints.

## When To Use

- kernel, driver, native memory, ABI/FFI, real-time behavior, syscall, or systems concurrency

## Do Not Use

- managed-runtime application work with no native or operating-system boundary
- C++ or Rust usage without a native ABI, OS, or resource boundary

## Required Inputs

- ownership/lifetime, ABI/callers, concurrency, platform/privilege, versions, consumers, threat model, and measurements

## Professional Decision Rules

- Preserve native ownership/lifetime, unsafe preconditions, ABI consumers, concurrency ordering, syscall/privilege, resource cleanup, arithmetic, and measured-performance invariants.
- Bound absence claims by the supported compiler/target/build matrix, analyzed state space, and unproved schedules, platforms, inputs, and foreign behavior.

## High-Value Gotchas

- ABI-compatible syntax can still change allocator ownership, callback lifetime, lock order, arithmetic behavior, or permitted recovery syscalls.

## Execution Checklist

1. Trace the affected native boundary and consumers.
2. Load named References for active decision problems.
3. Verify the selected mechanism within stated limits.

## Stop / Escalation Conditions

- Stop on unverified ownership, ABI consumers, concurrency topology, target, privilege, or recovery.
- Escalate exploitable memory, kernel/driver, deadline, or incompatible-consumer risk.

## Output Contract

- systems invariant, selected mechanism, safety/compatibility and measurement evidence, validation result, proof limits, unverified state space, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [ownership and concurrency contracts](references/ownership-and-concurrency-contracts.md) | targeted | native ownership, lifetime, unsafe preconditions, lock ordering, scheduling, or concurrency proof is open | no native ownership, unsafe boundary, lock ordering, scheduling, or concurrency decision exists | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, proof-limit, residual-risk |
| [abi platform and syscall contracts](references/abi-platform-and-syscall-contracts.md) | targeted | ABI representation, deployed consumers, target platform, syscall, privilege, sandbox, or partial I/O is open | C++ or Rust is mentioned without a native ABI OS or resource boundary | analysis-agent, task-agent, review-agent | boundary-decision, failure-decision, residual-risk |
| [resource lifecycle and error contracts](references/resource-lifecycle-and-error-contracts.md) | targeted | native resource lifecycle, partial initialization, error translation, retry, diagnostics, or recovery is open | no native resource, error, diagnostic, retry, or recovery decision exists | analysis-agent, task-agent, review-agent | decision-record, failure-decision, residual-risk |
| [performance and verification evidence](references/performance-and-verification-evidence.md) | evidence-pattern | low-level performance, measurement, validation, absence, or post-edit evidence needs closure | no low-level performance, validation, evidence, or absence claim is open | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [signals ffi atomics shared memory and fork](references/signals-ffi-atomics-shared-memory-and-fork.md) | targeted | signal, interrupt, FFI, unwind, atomic, shared-memory, DMA, fork, cancellation, or abnormal-error behavior is open | none of those signal, FFI, atomic, shared-memory, fork, cancellation, or abnormal-error behaviors changes | analysis-agent, task-agent, review-agent | boundary-decision, selected-approach, failure-decision, proof-limit, residual-risk |
