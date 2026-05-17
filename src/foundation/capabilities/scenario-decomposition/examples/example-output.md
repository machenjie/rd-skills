# Example Output

```markdown
## Scenario Matrix

| Type | Scenario | Expected Outcome | Evidence |
| --- | --- | --- | --- |
| Normal | Analyst exports active accounts for March | File contains only March-eligible active accounts | Integration test |
| Failure | Storage write fails after query succeeds | Export marked failed, no download link exposed | Job test and log assertion |
| Edge | No eligible accounts exist | Empty file with correct headers and zero-count summary | Contract test |
| Abuse | User requests export for another tenant | Request denied before job creation | Authorization test |
| Recovery | Worker retries after timeout | Duplicate file is not created | Idempotency test |
| Operational | Support inspects failed export | Failure reason is visible without exposing file contents | Manual support review |
```
