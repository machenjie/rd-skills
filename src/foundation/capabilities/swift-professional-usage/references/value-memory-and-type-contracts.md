# Swift Value, Memory, And Type Contracts

Use this checklist when identity, ownership, representation, or error behavior changes. It is not a Swift syntax guide.

## Decision Checklist

- **Value versus reference:** define semantic identity, mutation owner, copy independence and cost, and any stored references shared after copying.
- **Copy-on-write:** define shared storage, mutation detachment, uniqueness checks, nested-reference aliasing, and the boundary that leaves thread safety unproven.
- **ARC graph:** trace strong edges through closures, delegates, async work, timers, notifications, Objective-C objects, and caches; assign the edge that breaks each cycle.
- **Weak or unowned:** choose `weak` for valid absence and `unowned` only when every access requires a live referent with an accepted trap on violation.
- **Protocol/generic:** establish associated types, `Self` requirements, specialization needs, storage and heterogeneous collection needs, and the public compatibility surface.
- **Opaque/existential:** choose `some` for one hidden producer type or `any` for runtime-erased storage/dispatch, including the lost static relationships.
- **Optional:** define `nil` as a named state, safe binding/chaining or defaulting, forced-unwrapping preconditions, nested Optional behavior, and public/Objective-C API representation.
- **Error model:** list domain failures, cancellation, programmer faults, partial results, cleanup failure, and the exact boundary translating `throws`, `Result`, callbacks, or `NSError`.
- **Property wrapper:** identify backing storage, initialization order, projected API, mutation/observation owner, serialization behavior, and thread/isolation assumptions.

## Failure Probes

- Verify copy-on-write by copying an alias, mutating across its uniqueness boundary, and observing semantic independence, nested-reference aliasing, and allocation evidence.
- Release each owner in a closure/delegate/task cycle and prove teardown or the intended retained lifetime.
- Store the protocol existential, cross an associated-type boundary, and exercise the invalid lifetime of every `unowned` access.
- Exercise nil, present, nested Optional, failed conversion, chaining, defaulting, and invalid forced-unwrapping paths at each changed API boundary.
- Force each error category plus cleanup failure and confirm the caller can distinguish cancellation from domain failure.

## Primary Sources

- [Value and reference types](https://www.swift.org/documentation/articles/value-and-reference-types.html)
- [Structures and classes](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html)
- [Automatic Reference Counting](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/)
- [Protocols](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/)
- [Opaque and boxed protocol types](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/opaquetypes/)
- [Generics](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/generics/)
- [Error handling](https://docs.swift.org/swift-book/LanguageGuide/ErrorHandling.html)
- [The basics and Optionals](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/thebasics/)
- [Optional chaining](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/optionalchaining/)
- [Properties and property wrappers](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/properties/)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Swift.org and Swift Book pages are rolling; prove the repository's Swift language mode, compiler, standard library, deployment target, and package versions.
- Language rules do not prove copy-on-write cost, custom-storage uniqueness, retained-object lifetime, Objective-C annotations, framework observation, or source/binary compatibility for this project.
- Do not infer deep immutability from value syntax, safe lifetime from ARC, or concurrency safety from a locally accepted conformance.

## Required Record

- Record identity/copy representation, Optional state and unwrap/API outcomes, ownership graph, error mapping, invalid/teardown paths, version evidence, proof limits, and residual risk.
