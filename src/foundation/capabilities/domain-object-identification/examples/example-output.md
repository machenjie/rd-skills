# Example Output

```markdown
## Domain Object Decision

| Object | Classification | Identity or value equality | Lifecycle and invariant owner | Writer authority |
| --- | --- | --- | --- | --- |
| Account | Entity | `account_id` within tenant; stable across status changes | Account owns active-to-closed transition | Account command handler |
| ReportingPeriod | Immutable value object | Year, month, and timezone; no independent identity; change uses replacement semantics | Constructor protects valid range | No independent writer |
| MonthlyExport | Aggregate root | `export_id` | Aggregate update and invariant entry point; submitted snapshots cannot be replaced | Export command handler only |
| ExportFile | Resource boundary model | Provider `file_id` mapped to internal export identity | Export service owns availability | Provider callback translated by export adapter |

Rejected alternatives:
- ReportingPeriod is not an entity merely because persistence assigns a row id.
- ExportFile is not the domain aggregate merely because the API exposes it.
- Eligibility logic is not moved to a DTO, table model, or generic helper.

Relationships and mappings:
- MonthlyExport contains one ReportingPeriod value and references Accounts by identity.
- DTO, table, event, and provider-file mappings retain separate compatibility owners.

Evidence:
- Current command and repository writer scan cover handlers, jobs, persistence, events, schemas, and tests.
- Equality tests cover ReportingPeriod normalization and replacement.
- Aggregate tests deny writes that bypass MonthlyExport.

Proof limits:
- Uninspected operational scripts and unknown external consumers are not proven safe.

Residual risks:
- Confirm support-tool writer authority and event replay before changing lifecycle history.
```
