# Example Output

```markdown
## Prototype Brief

Purpose: Let a finance analyst create and monitor a monthly export.

Hierarchy:
1. Reporting period selection.
2. Eligibility summary and exclusions.
3. Submit action.
4. Job status and download action.

Layout intent:
- Use the existing report form pattern.
- Keep the summary adjacent to the submit action so the analyst can verify scope before creating the job.

Interaction contract:
- Submit creates one export job.
- Validation errors appear next to the period control and preserve input.
- Completed status exposes download.
- Failed status exposes reason and retry only when retry is safe.

Open decisions:
- Final empty-state copy requires product review.
```
