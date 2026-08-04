# JVM Execution And Boundary Contract

This contract focuses JVM review on runtime call paths, task lifecycle, classloading, serialization, and type boundaries that compilation or annotations do not establish.

## JVM Decision Matrix

| JVM facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Advice and transaction reachability | Runtime caller/callee path, proxy or weaving boundary, propagation, rollback, callback timing, and tested failure | Self-invocation, construction, callback, or scheduler path bypasses the expected interceptor |
| Interruption and cancellation | Task owner, interrupt consumer, status preservation or translation, blocking calls, timeout, cleanup, and caller outcome | Interrupted work continues, a broad catch clears status, or cancellation becomes a generic success/failure |
| Executor semantics | Owner, workload, admission, queue, rejection, thread/context propagation, task-failure observation, shutdown, and virtual-thread pinning evidence | Default/common pools or slogans hide backlog, lost context, unobserved failure, or incomplete drain |
| Classloader and scoped state | Loader/container lifecycle, static and thread-local state, reflective metadata, drivers, callbacks, caches, and cleanup | Reload or test isolation retains request data, resources, classes, or an obsolete loader |
| Null and type boundary | Java nullability annotations and bytecode signatures, boxed values, generic wildcards, collection elements, Optional use, records, reflection, and generated types | Annotation or compiler assumptions disappear across reflection, persistence, framework, or language boundaries |
| Serialization | Owning format/type/version contract, JVM unknown-field and polymorphic type-admission behavior, size/depth, numeric/time, classloader, and compatibility | Untrusted or historic payloads instantiate unexpected types or lose caller-visible meaning |
| Exception and resource path | Cause/category, async/reflection/proxy wrapping, transaction mapping, close/suppressed exceptions, and lifecycle owner | Wrapper layers erase retry/cancel meaning or cleanup failure replaces the primary error |
| Runtime proof | JDK/framework/container versions, changed call path, focused failure test, relevant runtime artifact, command freshness, and not-run residual | Compile success, annotation presence, or stale profile is used as runtime proof |

## Decision Limits

- For a JVM claim carried into handoff, cite current source, command, test, or artifact matched to the changed surface; otherwise mark it not run and name the residual risk.
- Virtual threads, collectors, proxy mechanisms, ORM behavior, and serializers are version- and workload-dependent candidates rather than universal defaults.
- Route transaction design, persistence, packages/builds, security, performance, and generic concurrency conclusions to their specialist owners.
