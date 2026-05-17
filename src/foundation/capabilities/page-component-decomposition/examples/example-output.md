# Example Output

```markdown
## Component Decomposition Map

Page owner:
- AccountSettingsPage coordinates route context, data readiness, and save workflow.

Components:
- SettingsHeader: renders title, status, and primary actions.
- ProfileFormSection: owns form field interaction and emits validated draft changes.
- NotificationPreferencesSection: renders preference controls from server-provided options.
- SaveBar: displays dirty state, submit progress, and recoverable errors.

State ownership:
- Server profile state is owned by the page data layer.
- Form draft state is owned by ProfileFormSection until submit.
- Dirty and submitting state are owned by AccountSettingsPage because they span sections.

Boundary decisions:
- Sections do not fetch data or navigate.
- SaveBar does not know field rules.
- No shared component is extracted until another page needs the same behavior.

Verification:
- Test save flow, validation errors, partial failure recovery, and permission-disabled controls.
```
