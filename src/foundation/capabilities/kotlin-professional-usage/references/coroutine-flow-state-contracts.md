# Kotlin Coroutine, Flow, And State Contracts

Use this reference to choose and verify Kotlin asynchronous ownership and state propagation. It is not a coroutine API catalog.

## Decision Matrix

| Decision | Required evidence | Failure signal |
| --- | --- | --- |
| Coroutine owner | Launch site, parent job, scope lifetime, dispatcher, child-failure policy, cancellation translation, cleanup, and shutdown | Detached work outlives its owner, cancellation becomes success, or a child failure is unobserved |
| Blocking boundary | Call-site evidence for blocking or suspending behavior, allowed dispatcher, interruption/cancellation bridge, and saturation behavior | Blocking work occupies a constrained dispatcher or ignores owner cancellation |
| Cold `Flow` | Producer restart and side effects per collector, collection lifetime, upstream completion/failure, buffering, and retry owner | Multiple collectors repeat expensive work or retry duplicates side effects |
| `SharedFlow` | Sharing owner, start/stop policy, replay, extra buffer, overflow, subscriber absence, and event-loss tolerance | An event is silently dropped, replayed to the wrong consumer, or retained without bound |
| `StateFlow` | Single mutation owner, initial/current value meaning, atomic update, equality conflation, and terminal-error representation | Concurrent writers lose transitions or an equal value is expected to emit |
| Compose bridge | State holder owner, snapshot-observable value, collector lifecycle, stable item identity, event path, and disposal | Collection outlives the screen, mutable non-state data stays stale, or recomposition repeats effects |

## Selection Rules

- Prefer structured child work when the result belongs to the caller; create a longer-lived scope only with an explicit lifecycle and shutdown owner.
- Preserve `CancellationException` semantics through broad catches, cleanup, and explicitly documented translation boundaries.
- Choose cold, shared, or state-bearing flow from producer lifetime and consumer guarantees, not from convenience.
- Model one-time events separately when replay, conflation, or subscriber absence would violate delivery semantics.
- Hoist Compose state to the lowest owner that reads and writes the transition; keep side effects keyed and lifecycle-bound.

## Required Proof

- Exercise normal completion, cancellation, producer failure, slow or absent consumer behavior, and owner teardown at the changed boundary.
- For shared state, include a concurrent update or deterministic transition proof and the first-subscriber behavior.
- For Compose, include state restoration or explicit non-restoration, disposal, and repeated-recomposition evidence where relevant.

## Primary Sources

- [Coroutines guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [Cancellation and timeouts](https://kotlinlang.org/docs/cancellation-and-timeouts.html)
- [Asynchronous Flow](https://kotlinlang.org/docs/flow.html)
- [Shared mutable state and concurrency](https://kotlinlang.org/docs/shared-mutable-state-and-concurrency.html)
- [State and Jetpack Compose](https://developer.android.com/develop/ui/compose/state)
- [Lifecycle of composables](https://developer.android.com/develop/ui/compose/lifecycle)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Kotlin and Android documentation is rolling; coroutine, Compose, lifecycle, compiler, and platform versions must be taken from the repository or runtime evidence.
- The sources establish API contracts and documented guidance, not the project's dispatcher capacity, lifecycle owner, delivery guarantee, or measured performance.
- Do not infer Android lifecycle behavior for platform-neutral Compose or backend Kotlin.
- Do not infer Kotlin/JVM behavior for other Kotlin targets.

## Required Record

- Record the owner, selected stream/state model, cancellation and failure outcomes, version evidence, exercised boundary, proof limits, and residual risk.
