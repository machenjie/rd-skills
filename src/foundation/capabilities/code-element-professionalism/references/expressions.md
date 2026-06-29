# Expressions

## Purpose

Use this reference when an expression's condition, assignment, grouping, defaulting, coercion, magic value, or side effect can affect correctness, security, data integrity, resource behavior, transaction order, or reviewability.

Expressions are professional when a reviewer can tell what value is computed, which states are intentionally distinguished, and which side effects are absent. Cleverness is not a substitute for visible intent.

## Decision Scope

Review expressions that participate in permissions, validation, persistence, cache/event/external I/O decisions, resource cleanup, user-visible state, API contracts, generated code, tests, and security boundaries.

Avoid complicated expressions when naming an intermediate decision improves reviewability. When an expression grows beyond local value computation into policy, side-effect order, or language-runtime semantics, route to the owning capability.

## Condition Expressions

Condition expressions should make the decision being tested visible. Repeated or business-significant conditions should become named predicates or named policy/domain decisions when the name improves reviewability and test targeting.

Do not mix validation, permission, mutation, defaulting, logging, metrics, cache writes, event publication, or external I/O inside a condition unless the language idiom is strong and the behavior is locally proven.

Conditions must distinguish missing/null/default from false, zero, empty string, and empty collection when those values have different domain meaning.

## Assignment Expressions

Do not hide assignment or mutation in a condition, return expression, lambda, comprehension, argument list, or ternary expression unless the idiom is strongly local, language-conventional, and tested or reviewed for that exact case.

Do not chain assignments. Chained assignment hides the owner of mutation, confuses aliasing, and makes later edits more likely to attach behavior to the wrong value.

When assignment is part of an expression because a language API requires it, keep it close to the read, avoid additional side effects, and state the variable's resulting state after the expression.

## Operator Precedence and Grouping

Do not rely on obscure precedence or mixed operators without parentheses. Parentheses must clarify intent, not hide an expression that should be split.

Mixed `and`/`or`, `&&`/`||`, nullish/optional chaining, arithmetic, comparison, bitwise, negation, membership, equality, and ternary operators are material when they decide behavior. If a reviewer must remember the precedence table to verify correctness, split or name the intermediate decision.

Do not depend on undefined or unspecified evaluation order. This is especially important when expressions include function calls, increments, property access, mutation, overloaded operators, macros, laziness, short-circuiting, or language-specific coercion.

## Truthiness, Nullish, and Default Semantics

Distinguish missing/null/default from false, zero, empty string, and empty collection. Use `??`, explicit `None`/`nil`/`null` checks, default parameters, or `or`/`||` only when their semantics match the domain.

Falsey-but-valid values must not be overwritten by a fallback. Empty-but-valid collections must not be treated as missing. Unknown, denied, expired, partial, and error states must not collapse into the same fallback unless the boundary contract says they do.

Defaulting expressions at public, API, configuration, permission, pricing, quota, retry, timeout, localization, or feature boundaries require tests or review proof for all meaningful value classes.

## Cast, Coercion, and Narrowing

Avoid lossy casts, narrowing conversions, and unsafe coercion. Conversions should preserve the domain state, units, precision, encoding, signedness, nullability, timezone, and range that the downstream code expects.

Coercive equality, implicit number/string conversion, truthiness conversion, enum fallback, pointer/reference casts, and type assertions must be justified by language convention and validation evidence.

When narrowing is necessary, keep the check next to the narrowed use or move it into a named validation boundary with tests.

## Magic Constants

Magic numbers, strings, dates, status values, retry counts, timeout values, money amounts, capacity limits, role names, and compatibility tokens require a named owner, unit, and concept when material.

Do not globalize a local constant merely to remove a literal. Place constants at the nearest owner that matches the policy or domain concept. Route to structure ownership when the constant's owner is unclear.

## Side-Effect Purity

Expressions should not hide I/O, cache mutation, persistence, event publication, time/random/env reads, logging callbacks, metrics callbacks, cleanup, or resource lifecycle changes.

Review whether an expression reads as pure. A mapper, getter, predicate, sort key, filter, serializer, display method, debug method, or validation expression that mutates state or performs I/O creates side-effect opacity and should route to side-effect flow or structure review.

If a side effect is intentionally embedded for a language idiom, tests must prove ordering, error behavior, and cleanup.

## Getter, Property, Debug, Display, and String Representation Expectations

Getter, property, `toString`, debug, display, representation, serialization, and descriptor-like expressions should be cheap, predictable, and side-effect-free unless framework convention explicitly says otherwise.

They must not perform persistence, network calls, cache writes, event publication, metric emission, lifecycle mutation, secret exposure, or expensive work without a documented framework owner and tests.

## Language Handoff

Hand off when expression behavior depends on:

- JavaScript or TypeScript `||`, `??`, optional chaining, coercive equality, assignment expressions, promises, getters, or strict null checks.
- Python truthiness, `or` defaulting, walrus assignment, comprehensions, descriptor properties, `__str__`, `__repr__`, or type narrowing.
- Go short declarations, zero values, nil interfaces, error wrapping, defer arguments, or map/slice aliasing.
- Java or JVM autoboxing, nullability annotations, Optional, streams, lambdas, property methods, or narrowing casts.
- Rust match guards, `Option`/`Result`, ownership moves, deref coercion, `as` casts, or trait display/debug behavior.
- C or C++ sequence points, unspecified evaluation order, overloaded operators, macros, casts, pointer arithmetic, RAII expression temporaries, or stream operators.

## Fix Patterns

- Split complicated conditions and name intermediate decisions.
- Replace repeated or business-significant conditions with a named predicate or policy/domain decision.
- Move assignments and mutations out of conditions, return expressions, argument lists, comprehensions, lambdas, and ternaries.
- Replace chained assignment with one assignment per concept.
- Add parentheses only for expressions that remain simple after grouping.
- Replace truthiness defaults with nullish or explicit missing-value checks when falsey values are valid.
- Replace unsafe casts and coercions with validated parsing or typed boundaries.
- Name magic constants with owner, unit, and concept at the nearest valid scope.
- Move I/O, cache mutation, event publication, time/random/env reads, logging, metrics, and cleanup into visible statements.

## Failure Modes

- `value || fallback` overwrites zero, false, empty string, or empty collection.
- A condition assigns a value and reviewers miss the mutation.
- Chained assignment aliases mutable state unintentionally.
- Mixed operators depend on a precedence table instead of visible intent.
- A language with unspecified evaluation order changes behavior across compiler/runtime versions.
- A cast loses precision, sign, timezone, unit, or nullability.
- A magic number becomes a hidden policy with no owner or tests.
- A getter, property, display, debug, mapper, or predicate performs I/O or mutation.

## Review Questions

- What value does this expression compute, and can that be named more clearly?
- Does the expression also mutate state, perform I/O, observe time/random/env, log, emit metrics, publish events, write cache, persist data, or clean up resources?
- Are missing/null/default, false, zero, empty string, empty collection, denied, expired, unknown, partial, and error states intentionally distinct?
- Are parentheses clarifying a simple expression or hiding one that should be split?
- Is any conversion lossy, coercive, narrowing, or language-specific enough to need a handoff?
- Does any magic value need a named owner, unit, and concept?

## Evidence

- Tests prove falsey-but-valid values are preserved and missing values default according to the domain rule.
- Tests or review proof covers mixed-precedence branches, repeated predicates, nested ternaries, and side-effect absence where material.
- Static analysis, compiler warnings, typecheck, linter, or review artifacts cover assignment-in-condition, chained assignment, unsafe coercion, magic constants, getter side effects, and undefined or unspecified evaluation order where available.
- Handoff names any language, side-effect, structure, security, or test capability that owns the remaining question.
