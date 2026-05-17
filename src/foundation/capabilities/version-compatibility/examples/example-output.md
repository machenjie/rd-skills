# Example Output

```markdown
## Compatibility Assessment

Surface: PaymentStatus enum in API and PaymentUpdated event.

Change:
- Add PENDING_REVIEW status.

Matrix:
- Old consumer with new producer: breaking unless unknown enum is tolerated.
- New consumer with old producer: safe.

Plan:
- First deploy consumers that treat unknown status as pending.
- Then deploy producers emitting PENDING_REVIEW behind a flag.
- Track event consumer errors and API client error rate.

Rollback:
- Disable producer flag.
- Keep consumer tolerance permanently.

Removal criteria:
- None. Unknown enum tolerance remains part of compatibility contract.
```
