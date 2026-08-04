---
name: swift-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for Swift ownership, concurrency, type, Objective-C interop, SwiftUI state, or package-boundary decisions."
---

# swift-professional-usage

## Registry Trigger

**Use when**

- Swift code changes value/reference or copy-on-write semantics, Optional APIs, ARC, actor isolation, `Sendable`, cancellation, type erasure, Objective-C interop, SwiftUI state, or module visibility.
- A compiler, deployment target, imported module, runtime, or UI lifecycle can change behavior beyond compilation.

**Do not use when**

- Swift appears only in comments/generated output, or another-language change has no Swift source or imported boundary.
- The change is only an iOS/macOS entitlement, signing, provisioning, packaging, or platform configuration with no Swift semantic decision.

## Skill Role

Own Swift language, memory, concurrency, type, interop, SwiftUI, and module semantics. Leave Apple platform/release contracts and generic concerns to their owners.

## High-Value Rules

- Choose value/reference and copy-on-write semantics from identity, aliasing, mutation isolation, copy cost, concurrency, and nested-reference evidence.
- Prove ARC teardown ownership across closures, delegates, callbacks, tasks, Objective-C edges, and cycle-breaking edges.
- Treat actor isolation and `Sendable` as access contracts; identify hops, unsafe escapes, inherited isolation, and UI owner.
- Preserve caller-visible cancellation semantics across task groups, unstructured tasks, continuations, and cleanup.
- Choose generics, `some`, or `any` from identity, storage, dispatch, associated-type, and compatibility needs.
- Define each Optional's absent-state meaning, safe unwrapping/defaulting, API exposure, and Objective-C import behavior.
- At Objective-C boundaries, inspect nullability, selector exposure, ownership, bridging copies, availability, and exception limits.
- In SwiftUI, bind state identity and lifetime to the correct view/model owner; prove observation, main-actor mutation, task cancellation, restoration, and package visibility.

## Anti-Patterns

- A `struct`, `let`, protocol, or `Sendable` conformance is treated as deep immutability or race-freedom proof.
- `weak`, `unowned`, or `[weak self]` is applied mechanically without proving lifetime and required work completion.
- `@MainActor` is treated as proof that every synchronous caller runs on the main thread.
- A detached task, continuation, or SwiftUI task hides cancellation, double resume, retention, or repeated effects.

## Stop Conditions

- Stop until behavior-controlling compiler, deployment, OS, package, Objective-C, and observation versions are known.
- Route entitlements, signing, lifecycle policy, notifications, background modes, and Apple platform APIs to their domain owner.
- Route generic concurrency, API evolution, security, persistence, performance, and testing to their owners.
- Stop on an unknown callback/continuation owner, isolation domain, Objective-C ownership annotation, or view identity.

## Output Contract

- Swift decision with identity ownership isolation cancellation type error interop SwiftUI module lifecycle invalid teardown outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [value memory and type contracts](references/value-memory-and-type-contracts.md) | targeted | Value/reference choice ARC protocol existential opaque generic or error semantics change | Identity ownership type representation and error boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [concurrency interop and ui contracts](references/concurrency-interop-and-ui-contracts.md) | targeted | Actor Sendable task cancellation continuation Objective-C SwiftUI state or package boundary changes | No concurrency interop UI-state or module-lifecycle behavior changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
