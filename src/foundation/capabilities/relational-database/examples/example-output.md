# Example Output

```markdown
## Relational Database Decision

Decision: Use relational tables for invoice issuance because invoice numbers,
account ownership, and payment status require constraints and transactional updates.

Constraints:
- invoices.account_id references accounts.id.
- invoices.invoice_number is unique per account.
- invoices.status is constrained to draft, issued, paid, void.

Transaction:
- Issue invoice and reserve invoice number in one local transaction.
- Use read committed plus unique constraint conflict handling for number allocation.

Indexes:
- account_id, status, issued_at supports account invoice list sorted by newest.
- Avoid indexing free-form notes because no production query uses it.

Migration:
- Add nullable issued_at, backfill in batches, then require it for new issued invoices.
```
