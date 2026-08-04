---
name: kotlin-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for Kotlin coroutine, Flow, type, interop, DSL, or Compose-state decisions; skip incidental Kotlin text."
---

# kotlin-professional-usage

## Registry Trigger

**Use when**

- Kotlin code changes coroutine ownership, `Flow`/`StateFlow`, null or Java interop, sealed/reified/value/data classes, delegated-property or DSL ownership, or Compose state.
- A compiler, coroutine, framework, generated, or Java boundary can change behavior beyond compilation.

**Do not use when**

- Kotlin appears only in comments/generated output, or a Java/JVM-only change has no Kotlin source.
- The change is only Android manifest, permission, packaging, signing, or other platform metadata with no Kotlin semantic decision.

## Skill Role

Own Kotlin language/library semantics. Leave shared JVM runtime to `java-jvm-professional-usage`, Android contracts to their domain owner, and generic concerns to specialists.

## High-Value Rules

- Give every coroutine a lifecycle owner, parent, dispatcher rationale, cancellation outcome, cleanup path, and observed failure.
- Decide whether a stream is cold, shared, or state-bearing; specify collection lifetime, replay/conflation, backpressure, failure, and slow-consumer behavior.
- Expose `StateFlow` as current state with an explicit mutation owner and atomic transition rule; do not use it as an unbounded event queue.
- Treat Java platform types and generated/reflection boundaries as unproven null contracts; validate or narrow them before Kotlin assumptions escape.
- Use sealed hierarchies, variance, and reified APIs only after proving closure, compatibility, and generated/reflective behavior.
- Check data/value-class equality, copy depth, boxing, mangling, and Java-callable ABI at every identity or interop boundary.
- Define each delegated property's owner, `getValue`/`setValue` effects, lifecycle, interop failure, and verification output.
- In Compose, locate state at its mutation/sharing owner; prove observability, identity, lifecycle-aware collection, and one-way events.

## Anti-Patterns

- `GlobalScope`, an unowned scope, or a default dispatcher hides cancellation, failure, or shutdown.
- A cold `Flow` is assumed to cache work, or `StateFlow`/`SharedFlow` is assumed to preserve every event.
- `!!`, a platform type, or a generated annotation is treated as runtime null proof.
- Data-class `copy`, a value wrapper, sealed `when`, or `remember` is treated as deep immutability, stable ABI, future exhaustiveness, or durable state.

## Stop Conditions

- Stop until behavior-controlling compiler, coroutine, Compose, Java-caller, and deployment versions are known.
- Route bytecode, classloading, JVM executor, GC, and shared runtime lifecycle to `java-jvm-professional-usage`.
- Route Android components, permissions, lifecycle policy, and packaging to the Android owner.
- Route concurrency, API compatibility, security, persistence, performance, and testing to their owners.

## Output Contract

- Kotlin decision with owner and caller paths coroutine stream state type Java ABI DSL Compose lifecycle invalid cancellation outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [coroutine flow state contracts](references/coroutine-flow-state-contracts.md) | targeted | Coroutine scope cancellation Flow StateFlow SharedFlow or Compose state changes | No asynchronous stream state holder or Compose collection behavior changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
| [type interop and dsl contracts](references/type-interop-and-dsl-contracts.md) | targeted | Nullability Java interop sealed/reified/value/data classes variance or DSL scope changes | Kotlin type and Java-callable boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
