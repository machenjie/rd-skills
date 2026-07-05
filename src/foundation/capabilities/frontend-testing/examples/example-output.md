# Example Output

```markdown
## Frontend Test Plan

Changed flow:
- User updates notification preferences.

Integration tests:
- Loads current preferences and renders available controls.
- Saves valid changes and shows success state.
- Shows field-level validation when a required channel is missing.
- Preserves unsaved changes after retryable save failure.

Permission tests:
- Viewer sees read-only controls and no save action.
- Admin sees editable controls.

API state tests:
- Loading skeleton appears before data.
- Timeout shows retry action.
- Stale save response does not overwrite newer edits.

E2E smoke:
- Admin opens settings from project page, changes one preference, saves, and refreshes to confirm persistence.
```
