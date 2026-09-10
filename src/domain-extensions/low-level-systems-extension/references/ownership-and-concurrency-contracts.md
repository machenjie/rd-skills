# Ownership and Concurrency Contracts

Use this Reference only for the named low-level ownership-and-concurrency-contracts decision.

## Decision Rules

- Define ownership, lifetime, allocation and deallocation pairing, aliasing, bounds, initialization, and unsafe-code preconditions across functions, threads, processes, languages, callbacks, and kernel boundaries.
- Map threads, locks, lock nesting, scheduler and priority behavior, ownership transfer, shutdown, deadlock, starvation, and priority inversion on reachable success and failure paths.
- Prove reachable wait cycles are excluded by the actual synchronization protocol, including reentrancy, callbacks, cancellation, cleanup, and teardown. An acyclic lock order is one proof; a protocol that removes hold-and-wait needs its own argument. Assess livelock and starvation separately. Runtime stress corroborates the argument; untested schedules remain residual risk.
