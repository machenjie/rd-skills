# Test Suite

## Required Checks

- Normal order display name uses existing formatter semantics.
- Missing customer information falls back to the established order label.
- Archived orders keep the legacy display behavior.
- Static or review checks reject new order business helpers in shared utils.

## Fixtures

- Active order with a customer display name.
- Archived order with legacy display text.
- Order record without customer details.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Reimplementing formatter logic locally should be rejected even if one test passes.
- Adding order behavior to `shared/stringUtils.ts` should fail review.
- Omitting reuse-search evidence should fail execution discipline review.