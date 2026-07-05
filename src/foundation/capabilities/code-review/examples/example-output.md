# Example Output

```markdown
## Code Review Findings

High: Missing authorization check in invoice export route
- Evidence: src/routes/invoices.py calls export_for_account without verifying account membership.
- Impact: A user could request another account export by id.
- Required fix: Check account access before export and add negative route test.

Medium: Generated client method does not exist
- Evidence: src/providers/payments.py calls client.refunds.create_bulk, but provider wrapper exposes create_refund only.
- Impact: Runtime failure on refund batch.
- Required fix: Use existing wrapper or add a tested wrapper method.

Approval status:
- Blocked until authorization and provider API issues are fixed.
```
