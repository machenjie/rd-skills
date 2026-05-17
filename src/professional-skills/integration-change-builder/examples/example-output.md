# Example Output

Integration: Payment provider webhook for subscription status.

Security: Verify signature and timestamp; reject replay outside five-minute tolerance.

Idempotency: Process event ID once and store final state.

Retries: Return non-2xx only for transient failures; dead-letter after bounded attempts.

Reconciliation: Nightly provider status sync compares local subscriptions.

Tests: valid signature, invalid signature, duplicate event, out-of-order event, provider outage.
