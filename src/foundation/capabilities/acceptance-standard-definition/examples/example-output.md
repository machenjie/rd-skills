# Example Output

```markdown
## Acceptance Standards

| ID | Condition | Action | Expected Result | Evidence | Blocking |
| --- | --- | --- | --- | --- | --- |
| AC-1 | User has finance role in tenant A | Run March export | File contains active tenant A accounts only | Integration test | Yes |
| AC-2 | User requests tenant B export | Submit export request | API returns authorization denial and no job is created | Authorization test | Yes |
| AC-3 | No eligible accounts exist | Run export | File has headers, zero rows, and zero-count summary | Contract test | Yes |
| AC-4 | Product asks for "better UX" | Review export status screen | Status uses approved empty, loading, failure, and success states | Design review checklist | No |

Rejected vague criterion:
- "Export works well" is not accepted without scenario and evidence.
```
