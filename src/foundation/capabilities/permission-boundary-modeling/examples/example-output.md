# Example Output

```markdown
## Permission Matrix

| Subject | Resource | Action | Condition | Decision | Enforcement |
| --- | --- | --- | --- | --- | --- |
| Finance analyst | MonthlyExport | create | Same tenant and finance role | Allow | Export API |
| Finance analyst | ExportFile | download | Same tenant and export completed | Allow | Download API |
| Finance analyst | ExportFile | download | Different tenant | Deny | Download API |
| Support agent | MonthlyExport metadata | read | Assigned support case | Allow | Support API |
| Support agent | ExportFile | download | Any tenant | Deny | Download API |
| Export worker | Account records | read | Job tenant and scoped service credential | Allow | Worker service |

Denial behavior:
- Return generic authorization denial without confirming resource existence.

Audit:
- Record create, download, support metadata read, and denial for cross-tenant attempts.
```
