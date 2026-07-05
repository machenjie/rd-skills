# Example Output

```markdown
## Business Rule Catalog

| ID | Rule | Owner | Enforcement | Evidence |
| --- | --- | --- | --- | --- |
| BR-1 | Standard monthly exports include only accounts active during the reporting period | Finance domain | Export eligibility service | Integration test |
| BR-2 | Audit exports include closed accounts when retention policy requires visibility | Compliance domain | Audit export policy | Policy review and contract test |
| BR-3 | A completed export file cannot be regenerated under the same export id | Export domain | MonthlyExport aggregate | Unit test |

Scattering risk:
- UI may display an eligibility preview but cannot be the source of truth.
- SQL may filter candidate accounts only after domain eligibility rules are named.
```
