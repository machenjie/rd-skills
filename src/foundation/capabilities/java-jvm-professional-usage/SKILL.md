---
name: java-jvm-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when JVM transactions, interruption, executors, classloaders, serialization, or null semantics change; skip generic work."
---

# java-jvm-professional-usage

## Registry Trigger

**Use when**

- Java source or shared JVM runtime behavior changes proxy/advice reachability, transaction behavior, interruption, executors, thread-local state, classloading, serialization, or Java null contracts.
- A JDK, framework, container, or generated boundary can change runtime behavior beyond what compilation proves.

**Do not use when**

- The open question is generic idiom, package/build policy, performance tuning, test portfolio, or transaction design without a JVM-specific semantic decision.
- No JVM source, configuration, generated surface, or runtime lifecycle changes.

## Skill Role

Prevent JVM-specific failures in advice reachability, interruption, executors, classloaders, thread-local state, null/type boundaries, serialization, and exception propagation. Leave architecture, persistence, public contracts, and generic concurrency to their owners.

## High-Value Rules

- Prove annotation-driven behavior from the runtime caller and proxy or weaving boundary; self-invocation can bypass advice.
- Preserve interrupt status or translate cancellation at an explicit task boundary.
- Give each executor owned admission, rejection, failure observation, context propagation, and shutdown behavior.
- Select virtual threads from workload and pinning evidence.
- Define cleanup ownership for static state, thread locals, executors, callbacks, and reflective caches across reload and shutdown.
- Define nullability, variance, and collection-element contracts across reflection, persistence, and generated boundaries.
- Bound serialization by format authority, versioning, polymorphism, unknown fields, size, depth, and compatibility.
- Preserve exception cause and category through async, reflection, proxy, transaction, and framework boundaries.

## Anti-Patterns

- Annotation presence is treated as proof that a transaction, async method, cache, or security interceptor ran.
- `InterruptedException` or task failure is swallowed, converted to a default, or logged without restoring the caller's cancellation semantics.
- A default executor or virtual-thread slogan hides admission, pinning, context, failure, or shutdown behavior.
- A static, thread-local, ORM proxy, serializer, or reflection cache retains request data, resources, or an obsolete classloader.

## Stop Conditions

- Route propagation, isolation, rollback, and after-commit design to `transaction-consistency`.
- Route ORM and data models to persistence owners.
- Route public serialization shape and version to the relevant contract owner.
- Route untrusted deserialization to `security-privacy-gate`.
- Route locks to `concurrency-control`, allocation to `language-performance-safety`, and tests to `language-testing-strategy`.

## Output Contract

- JVM decision with inspected caller/task paths, advice reachability, interruption, executor lifecycle, classloader/scoped state, null/type boundaries, serialization, exception/resource behavior, evidence and findings, proof limits, residual risk, and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A JVM change affects advice reachability interruption executor classloader null serialization or exception-resource semantics | The Java or JVM-runtime edit preserves established exception, resource, concurrency, class-loading, and serialization boundaries | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
