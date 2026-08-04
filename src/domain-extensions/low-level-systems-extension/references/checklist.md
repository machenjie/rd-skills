# Low Level Systems Extension Checklist

- Define ownership, lifetime, allocation and deallocation pairing, aliasing, bounds, initialization, and unsafe-code preconditions across functions, threads, processes, languages, callbacks, and kernel boundaries.
- Map threads, locks, lock nesting, scheduler and priority behavior, ownership transfer, shutdown, deadlock, starvation, and priority inversion on reachable success and failure paths.

A deadlock-freedom argument covers reachable reentrancy, callbacks, cancellation, cleanup, and teardown through an acyclic lock order. Runtime stress is corroborating evidence; untested schedules remain residual risk.
- Make ABI representation explicit: calling convention, symbol and version contract, struct and union layout, packing, alignment, padding, bit fields, endianness, word size, and serialization compatibility for deployed consumers.
- Cover supported OS, architecture, compiler, runtime, filesystem, network-stack, privilege, and permission differences that affect behavior or compatibility.
- Handle partial I/O, interruption, would-block results, timeout, cancellation, error mapping, kernel and user length validation, privilege changes, and sandbox behavior under its syscall contract.
- Track acquisition, transfer, exhaustion, and release of descriptors, sockets, handles, memory, threads, timers, mappings, temporary files, and kernel objects across partial initialization and shutdown.
- Preserve causal diagnostics and protocol state across error translation and retry while excluding secrets and invalid or partially initialized data.
- Tie optimization to a representative workload, baseline, variance, resource budget, and regression decision; preserve correctness, ABI, and tail behavior while changing structure.
- Select sanitizer, fuzz, race, stress, boundary, fault-injection, platform-matrix, and leak evidence from reachable undefined behavior, concurrency, parser, ABI, and resource risks.

Absence claims bind diagnostics to a supported compiler/target/build matrix and stated state space. Unproved inputs, schedules, platforms, and foreign-code behavior remain residual risk.
- Observe actionable crashes, panics, assertions, latency, throughput, memory, descriptor or handle pressure, retries, and recovery outcomes without exposing unsafe memory or secrets.
- For signal or interrupt contexts, identify platform-permitted operations, reentrancy, nesting or masking, deferred-work handoff, publication ordering, interrupted-state cleanup, and termination behavior. The contract reflects the target runtime and platform.
- At FFI and callback boundaries, contain panic, exception, and unwind behavior. The cross-runtime contract defines allocator pairing, ownership transfer, thread affinity, callback registration and revocation, context lifetime, and error translation.
- For atomics or shared memory, justify the selected memory order with required happens-before and publication relationships.
- For shared memory or DMA, define alignment, coherency, CPU and device ordering, producer and consumer ownership, visibility, and buffer lifetime.
- For fork, cancellation, or abnormal errors, define permitted continuation and cleanup or rollback ownership from inherited runtime, lock, thread, allocator, handle, and resource state. Evidence covers leaks, deadlock, double release, and use after lifetime end.
