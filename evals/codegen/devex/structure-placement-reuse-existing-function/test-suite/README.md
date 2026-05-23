# Test Suite

## Required Checks

- Mixed-case and whitespace-padded email input matches an existing normalized invitation.
- Tenant access denial prevents invite lookup and send behavior.
- No duplicate normalization helper is asserted by static review or structure evidence.
- Shared utils remain free of tenant and invitation business validation.

## Fixtures

- Existing invitation stored as `user@example.com`.
- Request input of ` User@Example.COM `.
- Tenant principal with no access to the target tenant.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Reimplementing normalizeEmail locally should be rejected by review even if tests pass.
- Adding tenant validation to shared utils should fail the structure rubric.
- Exporting an invitation-only helper should be rejected as unnecessary public API.
