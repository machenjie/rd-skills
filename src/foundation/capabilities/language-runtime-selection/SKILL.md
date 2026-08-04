---
name: language-runtime-selection
description: "`analysis-agent`/`task-agent`/`review-agent`: use when language/runtime choice changes semantics, concurrency, memory, deployment, or FFI; skip when runtime is fixed."
---

# language-runtime-selection

## Registry Trigger

**Use when**

- Selecting or adding a programming language or runtime can change workload fit, type and error semantics, concurrency, memory behavior, deployment, or interoperability.
- More than one repository-supported runtime remains feasible, or a new runtime is proposed to satisfy a hard constraint.

**Do not use when**

- The language/runtime is fixed and the open question is idiomatic usage, performance tuning, tests, packages, build mechanics, or configuration.
- The task changes a framework or platform without changing the programming language or runtime boundary.

## Skill Role

Select a language and runtime from workload fit, semantic guarantees, concurrency and memory model, ecosystem lifecycle, deployment artifact, cross-language boundaries, operational coverage, and exit risk. Exclude stack-wide platform selection.

## High-Value Rules

- Screen candidates against hard workload, latency, throughput, memory, startup, platform, safety, contract, deployment, and support constraints before comparing familiarity or preference.
- Treat the existing approved runtime as a candidate with known build, deploy, observability, and incident paths; a new runtime names the constraint or boundary advantage that justifies another lane.
- Compare runtime semantics across types, errors, numerics, serialization, and external boundaries without treating compile-time types as input validation.
- Compare threads, coroutines, event loops, scheduling, cancellation, backpressure, synchronization, and blocking behavior against the workload's failure and shutdown paths.
- Compare allocation and ownership, GC or manual memory behavior, resource cleanup, startup and initialization, artifact footprint, and crash or recovery behavior on target platforms.
- Verify package ecosystem, toolchain and platform support, lifecycle policy, supply-chain controls, profiler and debugger coverage, release upgrades, and accountable operational support.
- Define deployment, migration, rollback, and exit behavior plus any ABI/FFI, generated-contract, mixed-runtime-observability, or coexistence obligations the choice actually creates.
- Record versions, environment, sample, date, and unproved limits for benchmark and support claims.

## Anti-Patterns

- Popularity, team familiarity, or language reputation substitutes for workload and failure-mode evidence.
- A type system is treated as validation for untrusted or versioned external data.
- A prototype or public benchmark ignores the built artifact, deployment topology, scheduler, allocator, dependencies, or target concurrency.
- A new runtime hides another build/deploy lane, package ecosystem, incident toolchain, FFI ownership, or retirement obligation.

## Stop Conditions

- Route stack, comparison, package, build, configuration, idiom, runtime-safety, test, and native-boundary decisions to their named owners.
- Return an unresolved selection when candidate feasibility, representative measurements, platform support, operational ownership, coexistence safety, migration or rollback, or exit authority lacks current evidence.

## Output Contract

- language-runtime decision with selected candidate, rejected alternatives, hard-constraint evidence, workload and semantic fit, concurrency, memory, lifecycle, ecosystem, deployment, FFI, migration, rollback, exit, specialist routes, proof limits, residual risk, and unresolved owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing language-runtime candidates differ in semantics concurrency memory deployment ecosystem FFI lifecycle or exit behavior | The language runtime is fixed and no runtime boundary or migration decision changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
