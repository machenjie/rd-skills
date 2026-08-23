# Minimality Candidate Record

- Compare delete or omit, existing repository behavior, standard or native behavior, installed dependencies, direct local code, and new structure against the task's actual boundaries.

This record compares concrete implementation candidates against current acceptance, owner boundaries, and accident-prevention obligations.

## Candidate Comparison

| Candidate | Fit with current need | Rejection signal | Proof to retain |
| --- | --- | --- | --- |
| Omit or delete | Acceptance and protected obligations remain satisfied without the artifact | A reachable consumer, invariant, migration, recovery, or diagnostic path still depends on it | Consumer and generated-path search plus behavior-preserving tests |
| Existing repository behavior | One current owner already provides the needed semantics at the right boundary | Reuse would cross ownership, expose internals, or merge distinct policy | Owner, contract, caller, and rejected-reuse evidence |
| Standard or native behavior | Library, runtime, framework, browser, or database semantics match the required boundary | Version, portability, edge behavior, or operational ownership differs | Supported version and boundary-case comparison |
| Installed dependency | Present package closes a real capability gap without expanding policy or lifecycle | API, transitive surface, ownership, or compatibility cost exceeds direct behavior | Current version, approved owner, API fit, and supply-chain route |
| Direct local code | One cohesive owner can express the behavior without a reusable contract or lifecycle | Logic duplicates an owner, hides effects, or is likely to diverge across current consumers | Focused behavior test and same-pattern scan |
| New structure or dependency | Current variants, independent contract, lifecycle, or capability gap survive the nearer comparisons | The rationale is future flexibility, file count, aesthetics, or one trivial implementation | Current force, placement route, validation, rollback or deletion path, and residual risk |

## Boundary Checks

- Apply the ladder in order: delete or omit, existing repository behavior, standard or native behavior, installed dependency, direct local code, then new structure.
- Compare candidates across accepted behavior, authorization, data integrity, accessibility, compatibility, migration, observability, recovery, and incident evidence that the task can affect.
- Treat line count, file count, and abstraction count as investigation signals rather than proof of minimality.
- A single current implementation can still protect an independent external contract or lifecycle; the decision records that boundary instead of applying a numeric rule.
- Deletion and shrink claims state search limits for dynamic registration, reflection, generated code, stored data, and external consumers.
- Once structure is retained, hand owner-private placement to `implementation-structure-design`; hand a proved variation, lifecycle, protocol, concurrency, or extension force to `design-pattern-selection`.

## Anti-Patterns

- Reject speculative scaffolding, pass-through abstractions, duplicate packages/code, and shortcuts without a bounded exit.
