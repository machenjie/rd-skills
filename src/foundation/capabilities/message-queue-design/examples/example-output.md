# Example Output

```markdown
## Message Queue Plan

Topic: invoice-events
Consumer: invoice-email-worker

Delivery:
- At-least-once delivery.
- Ordering required only per invoice_id partition.

Idempotency:
- Deduplicate by event_id in inbox table for 30 days.
- Email send uses invoice_id plus template version as idempotency key.

Retry:
- Retry transient provider errors 5 times with jittered backoff.
- Validation errors go directly to dead letter.

Observability:
- Alert on consumer lag over 5 minutes or dead-letter count above zero.
```
