# Code Clarity Benchmarks And Patterns

Use this reference for L3+ clarity work, AI-generated/refactored code, file split/merge risk, high cognitive complexity, hidden side effects, or cross-module change-locality decisions.

## Benchmark Anchors

- **Google Engineering Practices readability review:** correctness comes first, but maintainability, simplicity, naming, comments, tests, and future-reader cost are first-class review concerns.
- **SonarSource cognitive complexity:** nested branches, boolean operators, switches, recursion, and control-flow breaks increase maintenance risk even when cyclomatic count looks acceptable.
- **Martin Fowler refactoring catalog:** extract function, decompose conditional, introduce parameter object, replace temp with query, and move function are tools for making intent and ownership visible.
- **Domain-Driven Design ubiquitous language:** condition names, policy names, constants, and test names should expose domain concepts instead of syntax or storage details.
- **Testing Library/xUnit readability practice:** tests should describe public behavior and protected regression intent, not implementation call order.

## Main-Flow Pattern Matrix

| Signal | Preferred Pattern | Escalate When | Evidence |
| --- | --- | --- | --- |
| Happy path buried by checks | Guard clauses or named precondition block | Checks carry authorization, transaction, or external side effects | Entry point, normal path, obscuring branches |
| Repeated condition or mode | Named policy predicate or parameter object | Current variants imply state machine or strategy boundary | Condition inventory, selected name, rejected abstraction |
| Long function | Extract by readable concept or keep as orchestration with reason | It mixes validation, decision, mutation, I/O, logging, mapping, and fallback | Responsibility map, side-effect map, validation evidence |
| Tiny helper chain | Inline, rename, or collapse weak helpers | Helpers are a true reusable boundary with owned tests | Call chain before/after, owner, next-change location |
| File split/merge | Split by owner boundary or merge only when cohesion improves | Public API, side effects, dependency direction, or tests get hidden | Opened files, imports/exports, behavior preservation |
| Comment-heavy code | Rename/extract first; retain why/contract comments | Comment explains security, compatibility, performance, fallback, or external quirk | Comment kept/rejected list and reason |

## Split/Merge Decision Rules

- A split is good when the entry point remains readable and each new file owns a concept, lifecycle, public contract, side-effect boundary, or test seam.
- A split is bad when a maintainer must jump through vague wrappers, one-function files, tiny policy fragments, or pass-through glue to understand one behavior.
- A merge is good when it restores cohesive flow and does not mix responsibilities, hide side effects, erase public/test boundaries, or reverse dependency direction.
- A merge is bad when it reduces file count while broadening the owner, hiding extension points, or making tests and callers harder to map.

## Complexity-Only Review Tags

Use these tags only when the requested task is explicitly complexity-only or when AI-generated code shows bloat:

| Tag | Use When | Required Proof |
| --- | --- | --- |
| `delete` | Code, flag, wrapper, branch, or fallback has no live owner | Caller/search evidence and validation impact |
| `shrink` | Equivalent readable behavior needs less structure | Before/after main-flow and validation evidence |
| `stdlib` | Custom code duplicates standard library behavior | API/version check and edge-case comparison |
| `native` | Platform/framework primitive is sufficient | Local convention and compatibility check |
| `existing-code` | Current utility/service already owns the behavior | Reuse search and rejected-copy rationale |
| `yagni` | Abstraction supports no current variant | Current caller/variant inventory and rollback path |

## Anti-Patterns

- "Readable enough" review that never names the public entry point or normal path.
- Boolean flags, `mode`, `kind`, or magic values that hide policy decisions at the call site.
- Helper bags with words like `utils`, `common`, `helpers`, or `misc` carrying business rules.
- File-count reduction used as evidence without owner, import/export, and test-boundary review.
- Tests that assert private helper call order, snapshots, or mock calls while public behavior can regress.
- Comments that narrate syntax while omitting the reason a surprising branch exists.
