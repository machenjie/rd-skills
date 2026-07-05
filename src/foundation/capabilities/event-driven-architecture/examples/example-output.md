# Example Output

```markdown
## Event Flow Plan

Flow: OrderPlaced -> inventory reservation projection.

Producer:
- Checkout writes order and outbox event in one transaction.

Ordering:
- Ordered per order_id only.
- Inventory consumer must tolerate cross-order reordering.

Idempotency:
- Consumer stores event_id before applying reservation.
- Replay skips already processed event_id.

Failure handling:
- Retry with exponential backoff.
- Dead-letter after configured exhaustion with alert to inventory owner.

Backpressure:
- Alert at five minutes of lag.
- Checkout remains available but inventory ETA is marked pending.

Quality gate: duplicate, replay, delayed, and dead-letter cases are tested.
```
