# Signals, FFI, Atomics, Shared Memory, and Fork

Use this Reference only for the named low-level signals-ffi-atomics-shared-memory-and-fork decision.

## Decision Rules

- For signal or interrupt contexts, identify platform-permitted operations, reentrancy, nesting or masking, deferred-work handoff, publication ordering, interrupted-state cleanup, and termination behavior. The contract reflects the target runtime and platform.
- At FFI and callback boundaries, contain panic, exception, and unwind behavior. The cross-runtime contract defines allocator pairing, ownership transfer, thread affinity, callback registration and revocation, context lifetime, and error translation.
- For atomics or shared memory, justify the selected memory order with required happens-before and publication relationships.
- For shared memory or DMA, define alignment, coherency, CPU and device ordering, producer and consumer ownership, visibility, and buffer lifetime.
- For fork, cancellation, or abnormal errors, define permitted continuation and cleanup or rollback ownership from inherited runtime, lock, thread, allocator, handle, and resource state. Evidence covers leaks, deadlock, double release, and use after lifetime end.
