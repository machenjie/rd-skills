# Ownership and Concurrency Contracts

Use this Reference only for the named low-level ownership-and-concurrency-contracts decision.

## Decision Rules

- Define ownership, lifetime, allocation and deallocation pairing, aliasing, bounds, initialization, and unsafe-code preconditions across functions, threads, processes, languages, callbacks, and kernel boundaries.
- Map threads, locks, lock nesting, scheduler and priority behavior, ownership transfer, shutdown, deadlock, starvation, and priority inversion on reachable success and failure paths.
- A deadlock-freedom argument covers reachable reentrancy, callbacks, cancellation, cleanup, and teardown through an acyclic lock order. Runtime stress is corroborating evidence; untested schedules remain residual risk.
