# Review Rubric

## Passing Standard

The solution must keep security-settings behavior in the owning feature,
reuse design primitives, and choose component, hook, prop, state, file, and
directory names that expose role and boundary.

## Scoring

- 30 percent feature-local versus shared placement accuracy.
- 25 percent naming discipline for component, hook, props, state, file, and directory.
- 20 percent state-scope and hook responsibility.
- 15 percent accessible user-behavior tests.
- 10 percent reuse of existing design-system primitives.

## Automatic Failure Conditions

- Adding security-specific copy or state to `components/common` or generic shared UI.
- Creating generic `useFeature`, `useData`, or `FeatureCard` abstractions for one flow.
- Naming non-trivial props or state `data`, `item`, `value`, or `info` when a security concept is known.
- Relying only on snapshot tests without render and dismissal behavior.

## Reviewer Notes

Strong answers classify each UI artifact as feature, component, hook, helper, or
shared primitive, then verify that names match repository vocabulary and
TypeScript/React conventions.
