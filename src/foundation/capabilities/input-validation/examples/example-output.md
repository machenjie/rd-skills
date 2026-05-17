# Example Output

```markdown
## Input Validation Contract

Endpoint: POST /accounts/{account_id}/invitations

Validation:
- account_id must be a UUID owned by the authenticated admin's tenant.
- email must be normalized, valid format, and under 254 characters.
- role must be allowlisted to viewer, editor, or billing_admin.
- billing_admin invite requires account owner approval.

Rejection:
- Unknown fields are rejected.
- Missing ownership returns 404-style safe denial.

Tests:
- Direct API call cannot invite into another tenant.
- Invalid role and oversized email are rejected.
```
