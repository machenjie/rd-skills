# Example Output

```markdown
## Information Architecture Plan

Primary task: Finance analyst reviews and exports monthly account data.

Structure:
- Reports
  - Monthly Exports
    - Export list
    - Export detail
    - Create export
  - Audit Exports
    - Audit export list

Navigation rules:
- Finance users see Monthly Exports.
- Compliance users also see Audit Exports.
- Support users see export metadata from account detail but no file download.

Label decision:
- Use "Monthly Exports" instead of "Account Export Jobs" because the task is reporting, not job management.

Risk:
- Hiding audit exports from finance users must not remove audit-mode export access for compliance.
```
