# Review Rubric

## Passing Standard

The solution must place order cancellation behavior at the correct owner,
preserve service orchestration boundaries, and treat names as architecture
evidence rather than style. A reviewer should understand why the chosen method,
service code, or helper belongs where it was placed.

## Scoring

- 30 percent ownership and method placement based on state, invariant, lifecycle, or collaborators.
- 25 percent preservation of OrderService authorization, transaction, and repository boundaries.
- 20 percent naming evidence and responsibility taxonomy.
- 15 percent boundary-focused tests for allowed and denied cancellation.
- 10 percent avoidance of shared utility and generic class pollution.

## Automatic Failure Conditions

- Adding order deadline or eligibility business logic to shared utils, common utils, or a generic helper package.
- Creating `OrderProcessor`, `CancellationHelper`, or equivalent stateless class without a real object responsibility.
- Naming public or non-trivial values `data`, `item`, `result`, or `handle` when order vocabulary is available.
- Testing only a private helper instead of observable order cancellation behavior.

## Reviewer Notes

Strong answers classify each new item as domain, service, helper, utility, or
test, then explain why the selected method or service placement protects an
invariant or coordinates a use case.
