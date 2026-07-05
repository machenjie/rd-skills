# Example Output

```markdown
## Use Case

ID: UC-Export-Create
Actor: Finance analyst
Goal: Generate a monthly export for the analyst's tenant.

Preconditions:
- Actor has export creation permission.
- Reporting period is closed.

Trigger:
- Actor submits the create export action.

Main path:
1. System validates period eligibility.
2. System creates a queued export job.
3. System shows export status.
4. Worker completes file generation.
5. Actor downloads completed file.

Alternate path:
- If no accounts are eligible, system generates an empty export with headers.

Failure path:
- If storage fails, export moves to failed and records a safe failure reason.

Postconditions:
- Export job has a durable terminal or recoverable state.
- Audit record links actor, period, and outcome.
```
