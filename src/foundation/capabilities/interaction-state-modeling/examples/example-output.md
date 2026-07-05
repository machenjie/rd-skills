# Example Output

```markdown
## State Matrix

| State | Trigger | User Behavior | Recovery | Evidence |
| --- | --- | --- | --- | --- |
| Loading | Export list request in flight | Existing filters remain visible; list area shows loading status | Wait or navigate away | Component test |
| Empty | Request succeeds with zero exports | Show empty list state and create action if permitted | Create export | Component test |
| Permission denied | User lacks export permission | No create action; restricted state explains lack of access | Request access through support path | Authorization E2E |
| Timeout | Submit status unknown | Show pending status, prevent duplicate submit, offer status refresh | Refresh status | Integration test |
| Success | Job complete and file available | Show download action and generated timestamp | Download file | E2E test |
| Partial | Summary count available, exclusions pending | Mark summary incomplete and disable submit | Wait or retry summary load | Component test |
```
