# Example Output

```markdown
## Idempotency And Retry Contract

Operation:
- Create order.

Idempotency:
- Key is required for POST /orders.
- Scope is customer id plus operation name plus key.
- Same key and same payload replays original response.
- Same key and different payload returns conflict.
- Retention window is 48 hours.

Retry:
- Retry transient storage timeout up to 3 attempts with bounded backoff and jitter.
- Do not retry validation, authorization, or inventory-unavailable failures.

Unknown outcome:
- If payment authorization times out, reconcile by provider reference before retrying.

Observability:
- Log idempotency key hash, attempt number, terminal state, and correlation id.
```
