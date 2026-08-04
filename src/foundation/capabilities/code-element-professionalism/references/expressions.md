# Expression Semantics

This guide resolves local expression hazards that can change permission, validation, persistence, resource cleanup, public behavior, or user-visible state.

## Expression Contract

| Expression hazard | Decision to expose | Accident signature |
| --- | --- | --- |
| Missing, default, or truthiness | Preserve distinctions among absent, false, zero, empty, unknown, denied, expired, partial, and error states | A falsey fallback overwrites a valid value or collapses different outcomes |
| Assignment or mutation | Keep mutation, resulting state, ordering, and cleanup visible at the owning statement boundary | Assignment in a condition, return, argument, or comprehension hides state or an effect |
| Precedence or evaluation | Make mixed operators, short-circuit behavior, laziness, overloads, and runtime evaluation order reviewable | A property access, macro, increment, or overloaded operator changes effect order |
| Cast, coercion, or narrowing | Preserve range, precision, signedness, unit, encoding, timezone, nullability, and domain identity | Lossy conversion, coercive comparison, or unchecked assertion changes meaning |
| Policy literal or default | Give material retry, timeout, quota, money, status, role, version, and date values an owner, unit, source, and nearest valid scope | A literal becomes hidden policy or a local constant is globalized to remove syntax |
| Read-like operation | Expose persistence, network, cache, event, metric, log, time, randomness, environment, or secret access behind a getter, predicate, mapper, or display conversion | Review assumes a cheap pure read while the expression performs work or leaks data |

## Proof And Routing

Exercise applicable value classes, conversion boundaries, ordering, error and cleanup paths, and side-effect absence. Type and static checks leave domain equivalence, runtime overload behavior, and unexercised schedules outside their proof.
Route language coercion and evaluation rules to `language-idiom-enforcement`, hidden effects to `data-side-effect-flow-tracing`, public shape to the API owner, and runtime cost or safety to `language-performance-safety`.
