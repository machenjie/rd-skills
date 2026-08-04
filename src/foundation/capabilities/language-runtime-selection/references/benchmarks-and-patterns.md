# Runtime Compatibility And Failure Matrix

This matrix compares feasible runtime candidates in the repository context through semantics, failure behavior, deployment, and owned lifecycle rather than language reputation.

## Runtime Decision Matrix

| Runtime facet | Facts that distinguish candidates | Rejection or residual signal |
| --- | --- | --- |
| Workload and budgets | Dominant and secondary workload axes, input shape, latency and throughput distributions, memory and startup budgets, and target platforms | Candidate evidence uses a different workload, topology, architecture, or release build |
| Language semantics | Type and nullability model, numeric behavior, errors and exceptions, serialization, runtime validation, and generated-contract compatibility | Static types or syntax reputation substitute for boundary and version-skew tests |
| Concurrency and scheduling | Threads, coroutines, event loop, scheduler, cancellation, backpressure, synchronization, blocking work, and shutdown | Queue growth, blocking, detached work, cancellation, or failure observation lacks an owner |
| Memory and resource lifecycle | Allocation and ownership, GC or manual memory, cleanup, finalization, artifact footprint, initialization, crash, and recovery | Pause, leak, lifetime, or startup behavior is assumed from the language name |
| Ecosystem and toolchain | Supported compiler/runtime and platforms, packages, integrity and license controls, build tools, profiler, debugger, sanitizer, and incident workflow | Required library, platform, diagnostic, or supply-chain capability is unsupported or unowned |
| Deployment and operation | Artifact and image shape, build/deploy lane, patching, observability, capacity, upgrade, support policy, and retirement | Another production lane is introduced without accepted operation and lifecycle cost |
| FFI and cross-language boundaries | ABI and toolchain compatibility, marshalling and copies, ownership, error and unwind behavior, schema validation, generated clients, and versioning | Native or cross-runtime behavior lacks contract, safety, compatibility, or rollback proof |
| Migration and exit | Coexistence, state and protocol movement, consumer order, rollback unit, information loss, and deletion path | Runtime replacement assumes a flag can reverse durable or consumer-visible changes |

## Decision Limits

- Measure the built candidate under representative workload and deployment conditions; public benchmarks and prototypes remain scoped feasibility evidence.
- Date lifecycle, ecosystem, vulnerability, and operational-coverage inputs, and record the trigger that makes them stale.
- Route chosen-language idioms, performance and safety, tests, packages, build/configuration, and native implementation details to their specialist owners.
