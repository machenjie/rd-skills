Review this relational data change:

The team adds a query over `invoice_events` with filters on `tenant_id`,
`created_at`, and `status`, then orders by `created_at DESC`. The table has
250M rows, no index plan, no EXPLAIN/ANALYZE output, and the test uses a tiny
development fixture.
