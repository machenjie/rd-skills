---
name: kotlin-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for Kotlin coroutine, Flow, type, interop, DSL, or Compose-state decisions; skip incidental Kotlin text."
---

# kotlin-professional-usage

## Registry Trigger

**Use when**

- Kotlin source changes coroutine, stream/state, type, Java interop, delegate, DSL, or Compose-state behavior.

**Do not use when**

- Kotlin is incidental, or only Android manifest, permission, signing, or packaging metadata changes.

## Skill Role

Own Kotlin language/library semantics; leave JVM runtime and Android policy to their owners.

## High-Value Rules

- When coroutine, cancellation, Flow, shared/state stream, or Compose-state decisions are active, load `coroutine-flow-state-contracts`.
- When nullability, Java interop, sealed/reified/value/data/variance, delegate, or DSL decisions are active, load `type-interop-and-dsl-contracts`.
- Bind the decision to current compiler/backend, libraries, caller, lifecycle owner, and target evidence.
- Stop on an unknown controlling version or boundary.

## Anti-Patterns

- Local compilation substituted for lifecycle, stream, type, or Java-caller evidence.

## Stop Conditions

- Route JVM runtime, Android policy, and generic concurrency, compatibility, security, persistence, performance, and testing to their owners.

## Output Contract

- Kotlin decision with owner and caller paths coroutine stream state type Java ABI DSL Compose lifecycle invalid cancellation outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [coroutine flow state contracts](references/coroutine-flow-state-contracts.md) | targeted | Coroutine scope cancellation Flow StateFlow SharedFlow or Compose state changes | No asynchronous stream state holder or Compose collection behavior changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
| [type interop and dsl contracts](references/type-interop-and-dsl-contracts.md) | targeted | Nullability Java interop sealed/reified/value/data classes variance or DSL scope changes | Kotlin type and Java-callable boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
