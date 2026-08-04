# Example Output

Integration: Payment provider webhook for subscription status.

Provider contract: `<provider-name>/<webhook-version>` defines `<signed-representation>` and `<permitted transformation or canonicalization>`.

Security: Preserve raw bytes only if that contract signs raw bytes. Verify the signature over the exact signed representation, freshness under `<provider-contract-derived freshness/replay window>`, and replay identity before any later representation change or effect.

Idempotency: Process event ID once and store final state.

Retries: Return non-2xx only for transient failures; dead-letter after bounded attempts.

Reconciliation: Nightly provider status sync compares local subscriptions.

Tests: valid signature, invalid signature, duplicate event, out-of-order event, provider outage.
