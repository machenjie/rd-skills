# Payment Trading Extension Checklist

- Server-side state, not frontend success, controls payment confirmation, entitlement, fulfillment, and balance changes.
- Idempotency keys cover create, retry, webhook, refund, adjustment, trade, and fulfillment operations.
- State machines define authorized, captured, settled, failed, canceled, refunded, disputed, reversed, expired, and reconciled states where relevant.
- Provider webhooks are authenticated, replay protected, ordered or safely reorderable, and auditable.
- Ledger entries are immutable, balanced, traceable to events, and reconciled against provider or exchange reports.
- Balance calculations define available, pending, reserved, settled, negative, and disputed amounts.
- Currency, precision, rounding, tax, time zone, settlement date, and cutoff rules are explicit.
- Permissions and maker-checker controls protect refunds, adjustments, payouts, and trading overrides.
- Reconciliation covers provider status, internal ledger, user-visible state, settlement files, and exception handling.
- Monitoring covers duplicate charges, failed webhooks, unreconciled entries, balance drift, refund failures, and dispute events.
