# Swift Concurrency, Interop, And UI Contracts

Use for a named isolation, task, Objective-C, SwiftUI, or package-boundary decision.

## Decision Matrix

| Boundary | Contract | Failure |
| --- | --- | --- |
| Structured task | Parent/children, inherited isolation, result/error aggregation, cancellation, cleanup, deadline. | Escaped child, hidden sibling failure, unchecked cancellation. |
| Unstructured task | Owner, captures, priority/task-local behavior, observed result, cancellation handle, teardown. | Stale mutation or work outliving owner. |
| Actor | Mutable state, sync/async entry, hops, reentrancy invariant, `nonisolated`, UI owner. | Suspension invalidates state or unsafe escape bypasses isolation. |
| `Sendable` | Stored/captured graph, generic constraints, synchronization, unsafe declarations, imported types. | Mutable reference crosses isolation unsafely. |
| Continuation | Exactly-once resume, cancellation race, callback lifetime, return isolation, error, resources. | Missing/double resume or post-cancel/wrong-owner result. |
| Objective-C | Nullability, selector, ownership, block lifetime, bridging copy, error, availability, caller. | IUO, copied collection, or retained callback changes meaning. |
| SwiftUI | View/model identity, state owner, observation, main-actor mutation, task cancellation, restoration, disposal. | Recreation, stale mutation, repeated effect, off-owner update. |
| Package/module | Owner, access/SPI/API, resource lookup, dependency direction, platforms. | Private detail becomes public or resource resolves in one host. |

## Required Proof

- Exercise completion, cancellation before/during suspension, owner teardown, and callback outcomes.
- Exercise actor reentrancy and affected unsafe/imported non-`Sendable` crossings.
- Exercise SwiftUI identity change, disappearance/reappearance, repeated render, and restoration or explicit non-restoration.

## Primary Sources

[Concurrency](https://docs.swift.org/swift-book/LanguageGuide/Concurrency.html), [Objective-C import](https://developer.apple.com/documentation/swift/importing-objective-c-into-swift), [nullability](https://developer.apple.com/documentation/swift/designating-nullability-in-objective-c-apis), [model data](https://developer.apple.com/documentation/SwiftUI/Managing-model-data-in-your-app), [State](https://developer.apple.com/documentation/swiftui/state), [StateObject](https://developer.apple.com/documentation/swiftui/stateobject), [packages](https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/introducingpackages/). Accessed 2026-07-24.

## Proof Limits

Rolling sources require current compiler/mode, strict concurrency, target, Objective-C SDK, observation, and package tools. `@MainActor` does not prove an arbitrary synchronous caller's thread. They do not prove annotations, availability, identity, packaging, or scheduling.

## Required Record And Rejections

- Record task/isolation owner, cancellation/continuation, imported boundary, UI/module lifecycle, failure paths, limits, residual risk.
- Reject annotations, detached tasks, continuations, or SwiftUI tasks as thread, cancellation, resume, retention, or effect proof.
