# Scala Types, Collections, and Effects

**Reference type:** targeted
**Load when:** Scala types, collection evaluation, Futures, or the selected effect library change execution or resource behavior.
**Do not load when:** The task is Java-only or has no Scala-specific type, evaluation, or effect decision.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** boundary-decision, validation-plan, proof-limit

## Scala Decisions

- Bind Scala major version, compiler options, collection library, and effect-library versions before applying syntax or runtime assumptions.
- Trace type inference, variance, implicit or contextual resolution, and conversions across the changed boundary.
- Check erased, reflective, and Java-interoperability boundaries against runtime values. A static type does not validate an external value.
- Distinguish strict collections, lazy views, and iterators. Repeated traversal can repeat work or consume a one-shot source.
- Preserve collection shape, ordering, and mutation visibility expected by callers. A seemingly equivalent collection operation can change these contracts.
- Bind a Future to its `ExecutionContext`. Blocking work can exhaust a fixed pool even when a global-pool example appears to succeed.
- Treat the effect of `blocking` as execution-context-dependent. This hint does not guarantee additional threads in an arbitrary executor.
- Compose dependent asynchronous steps through the required data dependency. Registered Future callbacks have no general execution-order guarantee.
- Observe failed asynchronous results and define ownership for work that outlives its caller. A timeout does not itself supply cancellation of arbitrary Future work.
- Load the actual effect library's cancellation and resource rules when that library is present. Future semantics are not a substitute for effect-runtime semantics.
- Keep resource use within its managed scope. Returning a value that captures a closed resource can violate a valid-looking static type.
- Preserve exception and cleanup outcomes across synchronous code, Future failures, and the selected effect's error channel.

## Distinguishing Cases

| Case | Observable check |
| --- | --- |
| Traverse a lazy view twice around a side effect | The chosen evaluation contract accounts for repeated execution |
| Run blocking work on a bounded executor | Dependent work can progress or the saturation failure is explicit |
| Register two callbacks and assume their order | The test exposes the absent sequencing dependency |
| Return a stream or closure from a closed resource scope | Later consumption cannot access an already released resource |
| Cross Java or reflective input with a narrow Scala type | Runtime null, element, and representation behavior matches the accepted input contract |

Return type and evaluation boundaries, execution-context choices, resource lifetime, and omitted runtime conditions.
Reuse JVM advice, interruption, and classloader guidance for shared JVM mechanisms.

## Version Sources

- Check [Scala Futures](https://docs.scala-lang.org/overviews/core/futures.html) and [Scala 2.13 collection views](https://docs.scala-lang.org/overviews/collections-2.13/views.html) against the target language version.
- For projects using Cats Effect 3.x, check [Resource scopes](https://typelevel.org/cats-effect/docs/std/resource); other effect libraries have their own contracts.
