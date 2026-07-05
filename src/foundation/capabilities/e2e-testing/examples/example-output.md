# Example Output

```markdown
## E2E Test Plan

Journey: Admin disables a project member.

Role: Organization admin.

Source evidence:
- Current member-management route and existing E2E folder inspected.
- Prior flaky member test rejected because CI artifact is stale after route rename.

Steps:
- Sign in as admin.
- Open project settings from the project detail page.
- Disable one active member.
- Confirm destructive action in modal.

Assertions:
- Member status changes to disabled.
- Disabled member cannot access the project after refresh.
- Audit entry appears with admin actor.

Flake controls:
- Unique project per run.
- Stable data-testid selectors.
- Trace and screenshot on failure.

Validation evidence:
- Command: `npx playwright test tests/e2e/member-disable.spec.ts`
- Exit code: not run yet; owner must run before release.
- Evidence limit: does not prove all roles, browsers, or production email delivery.
```
