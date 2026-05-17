# Example Output

```markdown
## Controller Implementation Plan

Operation:
- POST /orders

Controller responsibilities:
- Parse request body and idempotency header.
- Invoke CreateOrderRequest validation.
- Extract authenticated subject and request correlation id.
- Call CreateOrderService with validated command and auth context.
- Map Created result to 201 with Location header.
- Map validation failure to 400, unauthorized to 403, duplicate idempotency replay to prior response.

Forbidden in controller:
- Pricing calculation.
- Inventory reservation logic.
- Transaction management.
- Repository queries.

Tests:
- Valid request maps to service command.
- Invalid payload returns stable validation error.
- Service authorization denial returns client-safe 403.
```
