# Example Output

```markdown
## Error Catalog Entry

Code: REFUND_NOT_ALLOWED
Category: domain_conflict
Status: 409

User-safe message:
- This order cannot be refunded in its current state.

Client action:
- Show the message and refresh order state.

Retryability:
- Not retryable without a state change.

Internal mapping:
- RefundPolicyViolation.ORDER_CLOSED
- Do not expose internal policy name in response.

Traceability:
- Include correlation_id in response and structured log entry.
```
