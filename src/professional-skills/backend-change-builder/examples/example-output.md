# Example Output

Backend change: Archive project endpoint.

Validation: Project ID format and request idempotency key.

Authorization: User must own project or hold admin role for tenant.

Transaction: Update project status, write audit record, emit outbox event.

Failure handling: Retrying same idempotency key returns final archive result.

Tests: authorization matrix, duplicate retry, transaction rollback, event emission.
