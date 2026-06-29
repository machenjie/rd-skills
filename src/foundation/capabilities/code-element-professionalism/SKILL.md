---
name: code-element-professionalism
description: Reviews low-level code element choices for variables, expressions, and statements, and bridges function, class, method, file, and directory concerns to existing structure, clarity, language, review, refactoring, and test capabilities.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "129"
changeforge_version: 0.1.0
---

# Mission

Make individual code elements professional enough to be trusted in production changes: variables must have clear lifetime, initialization, scope, mutability, and sentinel semantics; expressions must make precedence, nullish/default, truthiness, comparison, and side effects visible; statements must preserve control-flow, resource, transaction, cleanup, and event-order correctness.

This capability owns low-level element decisions that are often too small for architecture review and too concrete for broad clarity review. It does not own module, object, file, directory, design-pattern, language-runtime, or end-to-end side-effect architecture decisions; it names those bridges and routes them to the existing capability that owns the larger boundary.

# When To Use

Use when code is written, reviewed, generated, refactored, or tested and any local element-level hazard appears:

- A variable may be uninitialized, shadowed, reused for an unrelated concept, mutated across a loop, or given a `null`/`None`/zero/empty sentinel without explicit semantics.
- An expression hides assignment, mutation, I/O, time, randomness, or unsafe conversion inside a condition, return value, comprehension, ternary, lambda, or argument list.
- Boolean, truthiness, nullish/default, comparison, mixed precedence, magic constant, or type coercion behavior decides a business, permission, security, resource, or transaction path.
- A statement has empty loop or branch behavior, implicit switch fallthrough, loop-counter mutation, overly broad try/catch/finally/defer scope, missing cleanup, or event/cache/external I/O before commit.
- Generated code looks plausible but uses local defaults, shadowing, hidden side effects, nested expressions, or broad exception statements that would pass shallow review.

# Do Not Use When

- The main question is where a function, method, class, file, directory, component, hook, repository, adapter, or module belongs. Use `implementation-structure-design`.
- The main question is broad readability, navigation cost, cognitive complexity, comments, or main-flow clarity after the local element hazard is named. Use `code-clarity-maintainability`.
- The main question is language-specific API, syntax, lifetime, ownership, async, pointer, nullability, concurrency, or runtime idiom. Use `language-idiom-enforcement` and the matching language/runtime capability.
- The main question is cross-boundary side-effect flow, transaction consistency, idempotency, caching, eventing, or external I/O ordering. Use `data-side-effect-flow-tracing`, `transaction-consistency`, or the owning integration/data capability.
- The main question is behavior-preserving movement or structural cleanup after the element problem is understood. Use `refactoring`.

# Non-Negotiable Rules

- Every variable used in behavior, permission, money, data mutation, resource, or transaction logic must have explicit initialization, scope, lifetime, mutability, and sentinel/default semantics.
- Do not reuse one variable for unrelated concepts or lifecycle phases. Introduce a precise name or a narrow scope when the value's meaning changes.
- Shadowing is acceptable only when local language convention and scope make it harmless; shadowing errors, permissions, resources, transactions, loop counters, or state variables requires proof or rewrite.
- Defaults must preserve meaning. `||`, `or`, `?:`, `??`, empty string, zero, empty collection, `null`, and `None` must not be interchangeable unless the domain says they are.
- Expressions that decide behavior must not rely on reader memory for mixed precedence, coercion, truthiness, negation, or hidden assignment. Parenthesize, name, or split when correctness depends on interpretation.
- Conditions, ternaries, comprehensions, lambdas, and argument expressions must not hide mutation, I/O, events, logging, metrics, time, randomness, or cleanup work.
- Magic constants in expressions require a named concept, owner, and unit when they affect business behavior, security, limits, retries, timeouts, money, capacity, or compatibility.
- Empty loops, empty branches, intentional switch fallthrough, ignored return values, and no-op catches must be explicit and justified by local convention or review evidence.
- Loop counters, iterators, cursor state, and collection mutation must not be modified in multiple places unless the invariant and termination proof are obvious or documented.
- Try/catch/finally/defer/cleanup scope must be as narrow as the risk allows, release all owned resources, and avoid swallowing errors or committing partial state silently.
- Events, cache mutations, external I/O, notifications, and irreversible side effects must not appear before the transaction/source-of-truth commit unless an owning capability proves that ordering.
- Function, class, method, file, and directory rules here are bridge checks only: this capability may flag a boolean trap, side-effect getter, weak method name, or local file constant, but placement and ownership route to structure capabilities.

# Industry Benchmarks

Anchor decisions against Google Engineering Practices code review guidance for readability and correctness; CERT C/C++ and C++ Core Guidelines for initialization, lifetime, fallthrough, and resource cleanup; Effective Go guidance on shadowing-sensitive error handling; PEP 8 and Python guidance on mutable defaults and clarity; TypeScript and JavaScript professional practice around `??` versus `||`, strict equality, and truthiness; SonarSource rules for cognitive complexity, nested conditionals, magic numbers, and empty statements; OpenSSF Scorecard and NIST SSDF review expectations for generated code and secure implementation evidence.

# Selection Rules

Select this capability when the defect or decision fits in one local code element or a short local element cluster. Use it with:

- `backend-change-builder` for request, permission, tenant, resource, transaction, cleanup, cache, event, and external I/O element hazards.
- `frontend-change-builder` for component state defaults, form truthiness, disabled/error branch expressions, async cleanup statements, and render-time side effects.
- `ai-code-review-refactor` when generated code uses suspicious defaults, shadowing, nested expressions, hidden assignments, no-op statements, or side-effect getters.
- `code-review` for severity-classified element findings in completed diffs.
- `refactoring` when the safest fix is to split an expression, narrow scope, rename/re-scope a variable, or isolate cleanup without changing behavior.
- `quality-test-gate` when tests must prove nullish/default, truthiness, fallthrough, cleanup, resource, or transaction ordering behavior.

Prefer adjacent capabilities when the problem exceeds a code element: `implementation-structure-design` owns signatures, placement, objects, files, directories, and boolean-trap API design; `code-clarity-maintainability` owns broad readability and navigation cost; `language-idiom-enforcement` owns language-specific idiom and runtime semantics; `data-side-effect-flow-tracing` owns cross-boundary side-effect maps.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when a variable, expression, or statement affects authentication, authorization, tenant isolation, trust boundaries, secrets, PII, output encoding, path handling, query construction, or request validation.
- Escalate to `data-side-effect-flow-tracing` or `transaction-consistency` when statement order involves commits, events, cache writes, message publication, external I/O, retries, idempotency, or partial failure.
- Escalate to `language-idiom-enforcement` and a language runtime capability when correctness depends on language-specific scoping, lifetime, pointer/reference, async, coroutine, exception, cleanup, ownership, or nullability semantics.
- Escalate to `implementation-structure-design` when an element issue reveals a bad function signature, boolean trap, side-effect getter/setter, wrong method owner, misplaced constant, or unclear file/module owner.
- Escalate to `code-clarity-maintainability` when local expression or statement fixes are insufficient because the main flow, nesting, or cognitive complexity remains hard to read.
- Escalate to `quality-test-gate` when the only evidence for an element decision is a claim; defaults, branch ordering, fallthrough, cleanup, and transaction/event ordering need executable or reviewable proof.

# Reference Loading Policy

Satisfy the Output Contract from the `SKILL.md` body unless the selected level below requires one or more deep references.

L1 inline-only: ordinary local naming/readability decisions with no initialization, default, side-effect, resource, control-flow, transaction, or concurrency risk.

L2 load exactly one matching element reference:

- Read [references/variables.md](references/variables.md) for initialization, scope, mutability, default, and lifetime risks.
- Read [references/expressions.md](references/expressions.md) for condition, assignment, operator, nullish, truthiness, cast, magic-value, and side-effect risks.
- Read [references/statements.md](references/statements.md) for control, resource, error, loop, transaction, and concurrency statement risks.

L3 load multiple selected references for AI-generated patches, code review/refactor, production paths, multi-language edits, side-effect order, resource cleanup, transaction/event/cache ordering, concurrency, or async risk.

L4/L5 routes involving security, regulated, money/trading, backend correctness, data integrity, migration, or production reliability paths must route to the owning safety, reliability, data, integration, or transaction capability and load this capability only for the local element portion.

Read [references/functions.md](references/functions.md), [references/classes.md](references/classes.md), [references/methods.md](references/methods.md), [references/files.md](references/files.md), or [references/directories.md](references/directories.md) only as bridge references before handing ownership to `implementation-structure-design`, `code-clarity-maintainability`, or `refactoring`. Read [references/open-source-benchmark-map.md](references/open-source-benchmark-map.md) for L3+ work, AI-generated patches, security-sensitive code, or benchmark authoring.

Do not load every deep reference by default. L2 and higher routes should name the selected element references, the skipped references, and why the skipped references are not needed.

# Critical Details

## Variable Decisions

Variables carry correctness through name, scope, initialization, lifetime, mutability, and default semantics. Inspect first assignment, every reassignment, every read-before-write possibility, closure capture, loop/cursor mutation, returned alias, cleanup owner, and sentinel branch. A variable name that stays the same while the value's concept changes is a hidden state machine.

## Expression Decisions

Expressions are professional only when a reviewer can see the value being computed and the side effects that are absent. Split expressions that mix behavior decisions with mutation, assignment, I/O, defaulting, type coercion, or broad precedence. Name domain decisions before repeating them; parenthesize only when it clarifies the actual operation rather than masking a too-complex expression.

## Statement Decisions

Statements own observable ordering. Review control-flow statements for empty behavior, fallthrough, loop termination, cleanup, and error propagation. Review transaction statements for source-of-truth commit order before event/cache/external I/O. A statement block that "usually works" but broadens error handling, cleanup scope, or event order is not complete.

## Bridge Element Decisions

Functions, classes, methods, files, and directories appear in this capability only when a low-level element exposes a local hazard: boolean trap parameters, side-effect getters, overloaded method names, file-scope mutable constants, or directory-level default/config confusion. The fix may be local, but ownership and placement decisions route outward.

# Failure Modes

- **Read-before-write variable:** a branch reads a variable that is initialized only in a different branch or exception path.
- **Shadowed state:** a local variable hides an error, context, transaction, permission, or resource variable that the outer scope still relies on.
- **Concept reuse:** one variable carries an ID, object, derived flag, and response value across a function.
- **Sentinel drift:** `null`, `None`, empty string, zero, false, empty collection, or default enum value silently changes business meaning.
- **Hidden assignment expression:** a condition or return expression mutates state while presenting as a predicate or value.
- **Precedence ambiguity:** mixed `&&`/`||`, `and`/`or`, arithmetic, comparison, bitwise, nullish, optional chaining, or negation relies on implicit precedence.
- **Truthiness bug:** a valid falsey value is overwritten, denied, or treated as missing.
- **Magic constant:** a retry, timeout, limit, status, permission, or money value appears without unit, owner, or concept name.
- **Empty or no-op statement:** an empty loop, catch, branch, or ignored return value hides intentional behavior from reviewers.
- **Fallthrough mistake:** switch/case or pattern matching continues into another branch without an explicit fallthrough contract.
- **Loop mutation hazard:** counter, iterator, cursor, collection, or termination state is changed in multiple places.
- **Broad try scope:** a catch handles more operations than it should and converts unrelated failures into the same result.
- **Cleanup gap:** file handles, streams, locks, subscriptions, timers, transactions, cursors, or temporary resources are not released on all paths.
- **Event before commit:** a statement publishes an event, writes cache, sends notification, or calls external I/O before the durable state change succeeds.
- **Side-effect getter:** a method or property that reads like access mutates state, performs I/O, or changes lifecycle.

# Output Contract

Return a Code Element Professionalism Review with:

- **Selected mode**: variable professionalism, expression professionalism, statement/control-flow professionalism, bridge review, or AI-generated code element review.
- **Element scope inspected**: files, functions, branches, variables, expressions, statements, and tests reviewed.
- **Variable assessment**: initialization, scope, lifetime, mutability, shadowing, concept reuse, sentinel/default, loop/cursor state, and closure capture decisions.
- **Expression assessment**: precedence, grouping, truthiness, nullish/default behavior, comparison/coercion, magic constants, hidden assignment/mutation/I/O, and named decision candidates.
- **Statement assessment**: loop/branch/switch behavior, try/catch/finally/defer scope, cleanup, ignored return values, transaction/event/cache/external I/O order, and side-effect visibility.
- **Bridge assessment**: function, method, class, file, or directory issue found and the owning adjacent capability selected, or a statement that no bridge escalation is needed.
- **Risk classification**: severity, affected behavior, security/data/resource/transaction impact, and whether the issue blocks completion.
- **Fix direction**: narrow scope, initialize earlier, rename/re-scope, split expression, name decision, add constant, isolate statement, narrow try scope, add cleanup, reorder side effect, or route to another capability.
- **Validation evidence**: tests, static analysis, typecheck, linter, review proof, or not-run disclosure showing the element behavior is covered.

# Evidence Contract

Close an element review only when it records:

- **Selected mode**: variable professionalism, expression professionalism, statement/control-flow professionalism, bridge review, or AI-generated code element review.
- **Source files inspected**: source files inspected, functions or branches inspected, and tests or fixtures reviewed before the element decision.
- **Element boundaries inspected**: variables, expressions, and statements in scope, plus any function, class, method, file, or directory bridge that defines the local boundary.
- **Local decision or escalation**: whether the element was fixed locally or handed off to `implementation-structure-design`, `language-idiom-enforcement`, `code-clarity-maintainability`, `data-side-effect-flow-tracing`, `transaction-consistency`, `security-privacy-gate`, or `quality-test-gate`.
- **Reuse / placement rationale**: why the element-level fix stays local, reuses an existing owner boundary, or escalates instead of creating a new structure rule here.
- **Behavior preservation**: whether behavior is preserved or intentionally changed, naming affected default, branch, cleanup, transaction, event, cache, or side-effect semantics.
- **Validation evidence**: validation command, static analysis, typecheck, linter, test output, or review artifact used as proof.
- **What evidence proves**: the exact variable initialization/default, expression truthiness/precedence/side-effect, or statement cleanup/event-order behavior covered.
- **What evidence does not prove**: remaining untested language-runtime, concurrency, transaction, security, integration, or production behavior.
- **Residual risk**: remaining uncertainty, owner, and whether it blocks completion.
- **Handoff and next gate**: the handoff target and next gate that must accept or close any remaining risk.

# Quality Gate

1. Variables used in material behavior are initialized before read, narrowly scoped, consistently named, and not reused for unrelated concepts.
2. Shadowing, mutation, and closure capture are harmless by local convention or removed.
3. Sentinel/default semantics distinguish missing, empty, false, zero, denied, expired, unknown, partial, and error states when those states differ.
4. Expressions that decide behavior make precedence, grouping, comparison, nullish/default, truthiness, and side effects visible.
5. Magic constants that affect behavior have names, units, and owning concepts.
6. Empty statements, intentional fallthrough, ignored return values, and no-op catches are explicit and justified.
7. Loops have clear termination, counter/cursor ownership, and mutation rules.
8. Try/catch/finally/defer scope is no broader than needed and cleanup covers success, failure, and early return.
9. Events, cache writes, notifications, and external I/O occur after source-of-truth commit unless an owning capability approves a different order.
10. Function/class/method/file/directory concerns are handed to the existing owner capability instead of being solved here by duplicating structure rules.
11. Tests or review evidence cover element behavior that can materially change correctness, security, data integrity, resource cleanup, or transaction ordering.

# Used By

`backend-change-builder`; `frontend-change-builder`; `ai-code-review-refactor`; `code-review`; `refactoring`; `quality-test-gate`; `change-forge-router`.

# Handoff

Hand off to `implementation-structure-design` for signatures, boolean-trap APIs, placement, method ownership, side-effect getters, files, and directories; `code-clarity-maintainability` for broad readability or cognitive complexity; `language-idiom-enforcement` for language-specific semantics; `data-side-effect-flow-tracing` and `transaction-consistency` for cross-boundary side-effect order; `security-privacy-gate` for trust-boundary element risks; `quality-test-gate` for proof strategy; and `refactoring` for behavior-preserving cleanup.

# Completion Criteria

The capability is complete when local code elements are reviewed with explicit variable, expression, and statement evidence; broader function, class, method, file, and directory ownership is routed to existing capabilities; validation or review proof covers material element risks; and the handoff names residual risk instead of treating a locally plausible expression or statement as professional code.
