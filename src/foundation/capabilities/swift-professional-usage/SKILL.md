---
name: swift-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for Swift ownership, concurrency, type, Objective-C interop, SwiftUI state, or package-boundary decisions."
---

# swift-professional-usage

## Registry Trigger

**Use when**

- Swift source changes identity, memory, type, concurrency, Objective-C, SwiftUI, or package behavior.

**Do not use when**

- Swift is incidental, or only entitlement, signing, provisioning, packaging, or platform configuration changes.

## Skill Role

Own Swift memory, concurrency, type, interop, SwiftUI, and module semantics; exclude Apple policy.

## High-Value Rules

- Select `value-memory-and-type-contracts` for active identity, ownership, ARC, copy, Optional, generic/existential, or error decisions.
- Select `concurrency-interop-and-ui-contracts` for active actor/Sendable, task/cancellation, continuation, Objective-C, SwiftUI, or package decisions.
- Bind decisions to current compiler/mode, target, modules, SDK, package, caller, and owner evidence.

## Anti-Patterns

- Compilation substituted for lifetime, isolation, imported-boundary, or package evidence.

## Stop Conditions

- Stop on unknown controlling version or boundary.
- Route Apple policy and generic risks to their owners.

## Output Contract

- Swift decision with identity ownership isolation cancellation type error interop SwiftUI module lifecycle invalid teardown outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [value memory and type contracts](references/value-memory-and-type-contracts.md) | targeted | Value/reference choice ARC protocol existential opaque generic or error semantics change | Identity ownership type representation and error boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [concurrency interop and ui contracts](references/concurrency-interop-and-ui-contracts.md) | targeted | Actor Sendable task cancellation continuation Objective-C SwiftUI state or package boundary changes | No concurrency interop UI-state or module-lifecycle behavior changes | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
