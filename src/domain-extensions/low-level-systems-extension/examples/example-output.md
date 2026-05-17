# Example Output

## Low Level Systems Domain Findings
- Blocking: the FFI boundary must declare ownership transfer and lifetime rules for the returned buffer.
- Concurrency requirement: document lock ordering and add a stress test for cancellation while I/O is pending.
- Syscall requirement: partial write, EINTR, timeout, and descriptor cleanup paths must be tested.

## Verification
- Sanitizer run for memory and undefined behavior on representative workloads.
- Race or thread sanitizer run for concurrent access paths.
- Benchmark comparing baseline and proposed implementation with regression threshold and leak detection.
