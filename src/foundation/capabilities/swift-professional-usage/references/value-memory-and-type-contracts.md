# Swift Value, Memory, And Type Contracts

Use for identity, ownership, representation, or error decisions.

## Decision And Probe Matrix

| Boundary | Contract and probe |
| --- | --- |
| Value/reference | Identity, mutation owner, copy independence/cost, shared references; copy then mutate across identity. |
| Copy-on-write | Storage sharing, detachment, uniqueness, nested aliases, unproved thread boundary; measure independence/allocation. |
| ARC | Strong edges through closure, delegate, task, timer, notification, Objective-C, cache; release owners, prove teardown/retention. |
| Weak/unowned | `weak` for valid absence; `unowned` under live-referent invariant. Test accepted trap in isolation; otherwise prove lifetime/teardown. |
| Protocol/generic | Associated type, `Self`, specialization, storage, heterogeneous collection, compatibility; cross affected type boundary. |
| Opaque/existential | `some` for one hidden producer type; `any` for erased storage/dispatch; record lost static relationships. |
| Optional | Named `nil`, binding/chaining/default, force precondition, nesting, public/Objective-C representation; exercise absent/present/invalid paths. |
| Error | Domain failure, cancellation, programmer fault, partial result, cleanup failure, `throws`/`Result`/callback/`NSError` translation; exercise each. |
| Wrapper | Storage, initialization, projection, mutation/observation owner, serialization, isolation; test API outcomes. |

## Primary Sources

[values](https://www.swift.org/documentation/articles/value-and-reference-types.html), [types](https://docs.swift.org/swift-book/LanguageGuide/ClassesAndStructures.html), [ARC](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/automaticreferencecounting/), [protocols](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/protocols/), [opaque](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/opaquetypes/), [generics](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/generics/), [errors](https://docs.swift.org/swift-book/LanguageGuide/ErrorHandling.html), [optional](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/thebasics/), [chaining](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/optionalchaining/), [wrappers](https://docs.swift.org/swift-book/documentation/the-swift-programming-language/properties/). Accessed 2026-07-24.

## Proof Limits

Sources require language mode, compiler, library, target, and packages. They do not prove copy cost, uniqueness, lifetime, Objective-C annotations, observation, compatibility, deep immutability, or concurrency safety.

## Required Record And Rejections

- Record identity/copy representation, Optional/API outcomes, ownership graph, error mapping, invalid/teardown, versions, limits, residual risk.
- Reject value syntax, ARC, `weak`/`unowned`, protocol, or `Sendable` as immutability, lifetime, or race-freedom proof.
