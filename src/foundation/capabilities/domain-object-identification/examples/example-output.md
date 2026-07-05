# Example Output

```markdown
## Domain Object Inventory

| Object | Category | Identity | Owner | Invariants |
| --- | --- | --- | --- | --- |
| Account | Entity | account_id | Tenant admin | Status must reflect lifecycle history |
| ReportingPeriod | Value object | year and month | Finance domain | Start date precedes end date |
| MonthlyExport | Aggregate | export_id | Finance analyst tenant scope | One submitted job has one eligibility snapshot |
| ExportFile | Resource | file_id | Export service | Download allowed only after completion |

Relationships:
- MonthlyExport references one ReportingPeriod.
- MonthlyExport includes many Account eligibility decisions.

Follow-up:
- Model MonthlyExport lifecycle as a state machine.
- Define permission matrix for file download.
```
