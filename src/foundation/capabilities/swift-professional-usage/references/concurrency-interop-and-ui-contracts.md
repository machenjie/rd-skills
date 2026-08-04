# Swift Concurrency, Interop, And UI Contracts

Use this reference to compare isolation, task, Objective-C, SwiftUI, and package-boundary choices that can alter observable behavior.

## Decision Matrix

| Boundary | Required evidence | Failure signal |
| --- | --- | --- |
| Structured task | Parent and child tasks, isolation inheritance, result/error aggregation, cancellation observation, cleanup, and deadline | Child work escapes, sibling failure is hidden, or cancellation is never checked |
| Unstructured or detached task | Explicit owner, retained captures, priority/task-local behavior, result observation, cancellation handle, and teardown | Fire-and-forget work mutates stale state or survives the feature owner |
| Actor or global actor | Isolated mutable state, synchronous and asynchronous entry points, hop sites, reentrancy invariant, `nonisolated` surface, and UI owner | State changes between suspension points or an unsafe escape bypasses isolation |
| `Sendable` crossing | Full stored/captured graph, generic constraints, reference synchronization, unsafe declarations, and imported types | A mutable reference crosses isolation under unchecked or inferred conformance |
| Continuation bridge | Exactly-once resume, cancellation race, callback lifetime, queue/isolation return, error translation, and retained resources | Missing/double resume, post-cancel callback, or result on the wrong owner |
| Objective-C boundary | Imported nullability, selector/name, ownership convention, block lifetime, bridging copy, error convention, availability, and caller | An implicitly unwrapped optional, copied collection, or retained callback changes meaning |
| SwiftUI state | View/model identity, state creation owner, observation mechanism, main-actor mutation, task key/cancellation, restoration, and disposal | Model recreation, stale non-observable mutation, repeated effect, or off-owner update |
| Package/module boundary | Target/module owner, access level, SPI/public API, resource/bundle lookup, dependency direction, and supported platforms | An implementation detail becomes public or a resource resolves only in one host |

## Required Proof

- Exercise normal completion, cancellation before and during suspension, owner teardown, and each callback outcome.
- Test an actor-reentrant path and every unsafe or imported non-`Sendable` crossing.
- For SwiftUI, exercise identity changes, disappearance/reappearance, repeated rendering, and restoration or explicit non-restoration.

## Primary Sources

- [Concurrency](https://docs.swift.org/swift-book/LanguageGuide/Concurrency.html)
- [Importing Objective-C into Swift](https://developer.apple.com/documentation/swift/importing-objective-c-into-swift)
- [Designating nullability in Objective-C APIs](https://developer.apple.com/documentation/swift/designating-nullability-in-objective-c-apis)
- [Managing model data in your app](https://developer.apple.com/documentation/SwiftUI/Managing-model-data-in-your-app)
- [State](https://developer.apple.com/documentation/swiftui/state)
- [StateObject](https://developer.apple.com/documentation/swiftui/stateobject)
- [Introducing packages](https://docs.swift.org/swiftpm/documentation/packagemanagerdocs/introducingpackages/)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Apple and Swift documentation is rolling; prove compiler/language mode, strict concurrency, deployment target, Objective-C SDK, observation model, and package-tools version.
- `@MainActor` specifies isolation, but the sources do not prove the thread of an arbitrary synchronous call or the project's caller path.
- Documentation does not prove callback annotations, runtime availability, view identity, resource packaging, or production scheduling for this project.

## Required Record

- Record the task/isolation owner, cancellation and continuation behavior, imported boundary, UI/module lifecycle, exercised failure paths, proof limits, and residual risk.
