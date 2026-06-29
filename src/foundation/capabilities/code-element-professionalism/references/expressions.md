# Expressions

Use this reference when precedence, grouping, truthiness, nullish/default behavior, comparison, coercion, nested expression shape, or hidden side effects can affect correctness.

## Decision Checks

- Identify the value the expression computes and whether it also mutates state, performs I/O, observes time/randomness/env, logs, emits metrics, or triggers cleanup.
- Split expressions that combine assignment, mutation, defaulting, conversion, permission decisions, or side effects.
- Parenthesize mixed precedence only when the expression remains simple; otherwise name intermediate decisions.
- Treat `||`, `or`, `?:`, `??`, `?.`, `&&`, `and`, negation, bitwise operations, and comparison chaining as material when they control behavior.
- Distinguish missing from false, zero, empty, denied, expired, and unknown before accepting truthiness.
- Replace repeated complex expressions with a named domain/policy decision when the name improves reviewability.
- Replace nested ternaries or comprehensions when a reviewer cannot map each branch to a requirement.
- Name magic constants with unit, concept, and owner when they affect limits, retries, timeouts, money, permissions, statuses, or compatibility.

## Fix Patterns

- Split side-effect expressions into statements before or after the decision point.
- Introduce a named predicate for repeated or business-significant conditions.
- Use nullish/default operators that match the domain's missing-value semantics.
- Add explicit comparisons when truthiness would conflate valid values.
- Extract constants only to the nearest owner; do not globalize local policy values without structure review.

## Evidence

- Tests prove falsey but valid values are preserved.
- Tests or review proof covers mixed-precedence branches and nested expression alternatives.
- Static analysis or lint rules cover assignment-in-condition, coercive equality, empty/no-op expressions, or magic constants where available.

