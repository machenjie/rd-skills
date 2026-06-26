# Example Output

```markdown
## Design System Rules

Mode selected:
- Existing component selection with accessibility-critical states.

Source evidence:
- Current design-system stories inspected: ReportForm, StatusBadge, InlineAlert, Button.
- Repository graph memory: prior export job status pattern accepted after current Storybook confirmation.
- No live browser, axe, Lighthouse, or screen-reader run in this planning pass.

Reuse:
- Existing ReportForm for period selection.
- Existing StatusBadge for export job states.
- Existing InlineAlert for validation and system errors.

Allowed variants:
- StatusBadge: queued, running, failed, complete.
- Button: primary submit, secondary cancel, danger only for destructive cancellation.

Accessibility:
- Status changes announce politely when job state changes.
- Disabled submit includes reachable explanation when eligibility summary is incomplete.
- WCAG in scope: 2.4.7 Focus Visible, 3.3.1 Error Identification, 4.1.2 Name/Role/Value, 4.1.3 Status Messages.

Responsive behavior:
- Summary appears above actions on narrow screens.
- Primary action remains after required inputs and before status history.

Validation map:
- StatusBadge states -> Storybook state story and visual regression.
- Disabled submit explanation -> keyboard test and accessible description assertion.
- InlineAlert errors -> axe plus role/alert assertion.
- Mobile action order -> viewport screenshot or Playwright check.

New component decision:
- No new component justified.

Handoff and limits:
- Hand off to frontend-testing for executable state, keyboard, and accessibility checks.
- This review does not prove real browser rendering, physical device hit targets, or screen-reader output until those validators run.
```
