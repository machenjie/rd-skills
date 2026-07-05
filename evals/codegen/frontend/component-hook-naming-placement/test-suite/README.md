# Test Suite

## Required Checks

- Recovery-code reminder renders for a user who has not generated codes.
- Dismiss action hides the reminder and preserves state across rerender.
- Accessible role and name queries are used instead of snapshots only.
- Structure evidence rejects generic shared component or hook placement.

## Fixtures

- Security settings user with recovery codes missing.
- Security settings user with recovery codes already generated.
- Local dismissed state for the current feature flow.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Adding security copy to `components/common` should be rejected.
- Creating `useFeature` or `useData` should fail the naming rubric.
- Snapshot-only tests should be rejected as insufficient evidence.
