# Example Output

```markdown
## API Contract Specification

Operation: Create refund
Method: POST
Path: /v1/orders/{order_id}/refunds

Auth:
- Requires order:refund permission for the tenant.

Request:
- idempotency_key: required string
- amount: required decimal
- reason: required enum

Responses:
- 201 RefundDTO when created.
- 200 RefundDTO when the same idempotency key is replayed.

Errors:
- REFUND_NOT_ALLOWED when order state blocks refund.
- REFUND_AMOUNT_EXCEEDS_CAPTURED when amount is invalid.

Compatibility:
- Additive fields only in v1 responses.
- Breaking behavior requires v2 or compatibility bridge.
```
