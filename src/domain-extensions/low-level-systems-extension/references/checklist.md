# Low Level Systems Extension Checklist

- Ownership, lifetime, allocation, deallocation, aliasing, bounds, and unsafe code assumptions are explicit.
- Concurrency model covers locks, atomics, memory ordering, thread lifecycle, cancellation, deadlock, starvation, and priority inversion.
- ABI and FFI boundaries cover struct layout, alignment, calling convention, symbol versioning, serialization, and compatibility.
- Platform behavior covers OS versions, architecture, endianness, word size, filesystem, network stack, and permission differences.
- Syscall handling covers partial reads/writes, EINTR, EAGAIN, errno mapping, timeout, signals, privilege, and sandboxing.
- Resource cleanup covers descriptors, sockets, handles, memory, threads, timers, mmap, temp files, and kernel objects.
- Error handling preserves diagnostics without leaking secrets or corrupting protocol state.
- Performance evidence includes benchmark workload, baseline, variance, regression threshold, and resource budget.
- Tests include sanitizer, fuzz, race, stress, boundary, fault injection, platform matrix, and leak detection where applicable.
- Observability covers crashes, panics, assertion failures, latency, throughput, memory use, descriptor count, and retry failures.
