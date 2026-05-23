# Review Rubric

## Passing Standard

The implementation must keep billing-specific UI and state in the billing
feature, reuse existing design primitives, and prove the behavior with
user-facing tests.

## Scoring

- 30 percent placement correctness for feature-local component, hook, and state.
- 25 percent behavior for render, dismiss, and persistence.
- 20 percent test quality using accessible queries and user interactions.
- 15 percent design system reuse without creating a one-off shared component.
- 10 percent API/state layering and minimal imports.

## Automatic Failure Conditions

- Adding billing-specific copy or rules to components/common.
- Creating a global useProductTour hook for a single feature.
- Moving feature-local state into the global store without cross-feature ownership.
- Tests only snapshot markup and do not prove dismissal behavior.

## Reviewer Notes

Strong answers separate presentational composition from persistence concerns and
only promote code to shared UI when there is a stable, business-neutral contract.
