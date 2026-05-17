# Example Output

```markdown
## User Flow Model

Actor: Finance analyst.
Goal: Create monthly export.

Entry points:
- Reports > Monthly Exports > Create.
- Account detail > Create export for selected period.

Main path:
1. Select reporting period.
2. Review eligibility summary.
3. Submit export.
4. View export status.
5. Download completed file.

Branches:
- Permission denied: show restricted action state and no job creation.
- Validation failure: keep selected period and show field-level reason.
- Timeout after submit: status page shows pending job and allows refresh.
- Cancellation before submit: return to export list with no state change.
- Back from status: return to export list with previous filters preserved.

Verification:
- E2E test covers success, permission denial, and timeout recovery.
```
