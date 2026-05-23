# Test Suite

## Required Checks

- Billing tour renders with accessible banner or region semantics.
- User can dismiss the tour with an accessible button.
- Dismissal state persists for the feature according to the chosen local storage or feature data path.
- No billing-specific copy or state is added to common components, generic hooks, or global store.

## Fixtures

- Billing settings user with tour not dismissed.
- Billing settings user with tour already dismissed.
- Existing design primitives for banner and button rendering.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Adding billing-specific copy to components/common should fail review.
- Creating a global useProductTour hook for one feature should fail structure review.
- Snapshot-only tests should fail because dismissal behavior is unproved.
