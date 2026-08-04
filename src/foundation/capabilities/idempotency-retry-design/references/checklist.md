# Idempotency Retry Design Checklist

- Inventory logical operations and the clients, brokers, providers, workflows, operators, or recovery paths that can repeat them.
- Bind identity to the required principal, tenant, subject, operation, canonical request meaning, and version behavior.
- Inventory business and external side effects; map record/effect/publication/acknowledgement ordering and each reachable crash window.
- Define ownership and caller-visible behavior for pending, succeeded, failed, and unknown states under same-identity concurrency.
- Define result reuse, conflict behavior, authorization, and information exposure for repeat observations.
- Identify the authoritative status source and safe action after timeout, cancellation, or transport loss when commit status is not proven.
- Define retention, expiry, tombstone, late-replay, backfill, and disaster-recovery behavior from the identified replay sources.
- Bound aggregate attempts, elapsed work, concurrency, pacing, and cancellation across the retrying layers in scope.
- Name the owned terminal, reconciliation, compensation, manual recovery, or accepted-loss path.
- Test concurrent duplicates, payload/version conflict, crash windows, unknown outcomes, late replay, exhaustion, and owner recovery.
- Record externally owned effects and residual duplicate-or-loss risk that current evidence cannot close.
