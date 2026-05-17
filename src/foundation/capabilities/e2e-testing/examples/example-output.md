# Example Output

```markdown
## E2E Test Plan

Journey: Admin disables a project member.

Role: Organization admin.

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
```
