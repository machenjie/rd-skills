# Example Output

```markdown
## Design System Rules

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

Responsive behavior:
- Summary appears above actions on narrow screens.
- Primary action remains after required inputs and before status history.

New component decision:
- No new component justified.
```
