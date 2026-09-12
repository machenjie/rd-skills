---
name: java-jvm-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when JVM transactions, interruption, executors, classloaders, serialization, or null semantics change; skip generic work."
---

# java-jvm-professional-usage

## Registry Trigger

**Use when**

- Inspect or change Java source or shared JVM proxy/advice reachability, transaction behavior, interruption, executors, thread-local state, classloading, serialization, or Java null contracts.
- A JDK, framework, container, or generated boundary can change runtime behavior beyond what compilation proves.

**Do not use when**

- The open question is generic idiom, package/build policy, performance tuning, test portfolio, or transaction design without a JVM-specific semantic decision.
- No task-local JVM source, configuration, generated surface, or runtime lifecycle requires inspection or change.

## Skill Role

Protect JVM runtime semantics. Leave architecture, persistence, public contracts, and generic concurrency to their owners.

## High-Value Rules

- Verify runtime callers through proxies or weaving; self-invocation can bypass advice.
- Preserve interrupt status or translate cancellation at an explicit task boundary.
- Own executor admission, rejection, failure observation, context propagation, and shutdown.
- Select virtual threads from workload and pinning evidence.
- Define cleanup ownership for static/thread-local state, executors, callbacks, and reflective caches through reload and shutdown.
- Define nullability, variance, and collection-element contracts across reflection, persistence, and generated boundaries.
- Bound serialization by format authority, versioning, polymorphism, unknown fields, size, depth, and compatibility.
- Preserve exception cause/category across async, reflection, proxies, transactions, and frameworks.

## Anti-Patterns

- Annotations are mistaken for advice execution.
- Swallowed interruption, substituted defaults, or logging alone lose cancellation.
- Executor or virtual-thread defaults hide lifecycle obligations.
- Cached/thread-local state retains requests, resources, or obsolete classloaders.

## Stop Conditions

- Return propagation, isolation, rollback, and after-commit design to `transaction-consistency`.
- Return ORM/data models to persistence owners; public serialization shape/version to contract owners.
- Escalate deserialization to Main/`security-privacy-gate` when type admission, trust, executable sinks, authority, resource exhaustion, or privacy changes leave control/proof unresolved.
- Keep ordinary format/compatibility validation with its owner.
- Return locks, allocation, and tests to `concurrency-control`, `language-performance-safety`, and `language-testing-strategy`, respectively.

## Output Contract

- JVM decision with inspected caller/task paths, advice reachability, interruption, executor lifecycle, classloader/scoped state, null/type boundaries, serialization, exception/resource behavior, evidence and findings, proof limits, residual risk, and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A JVM change affects advice reachability interruption executor classloader null serialization or exception-resource semantics | The Java or JVM-runtime edit preserves established exception, resource, concurrency, class-loading, and serialization boundaries | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
