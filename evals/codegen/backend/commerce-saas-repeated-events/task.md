# Task Contract

Implement three pure functions in `commerce_saas.py`.

## Order evaluator

`reconcile_order(capacity, events)` handles one finite resource order. Events have `id`, `kind`, and integer `at`. Exact repeated identities are idempotent. Conflicting payloads for one identity raise `ValueError`. Process unique events by `(at, id)`.

`reserve` supplies positive `quantity` and `expires_at`; one reservation is active at a time. Expiry occurs before any event at or after the deadline. `pay` records financial success but does not allocate or fulfill resources. `fulfill` needs payment and sufficient reserved units. An unsupported fulfillment records `unbacked-fulfillment` without mutation. Payment without reservation or earlier fulfillment records `late-payment`. `cancel` releases remaining reserved units once. `return` supplies quantity and `restock`; it cannot exceed outstanding fulfillment. Non-resalable returns become `retired`. `refund` changes financial state only. `tick` advances time.

Return available, reserved, cumulative fulfilled/returned, retired, outstanding, three state strings, and a set of issue codes. Preserve `capacity = available + reserved + outstanding + retired`. Negative or noninteger quantities and invalid reservation or return domains raise `ValueError`. Inputs remain unchanged.

## SaaS evaluator

`evaluate_saas(policy, events, now, observed_entitled=None)` evaluates the explicit policy. Ignore future received events. Lifecycle `cancel`/`restore` uses the greatest authoritative `revision`, not arrival order. Financial events are `paid`, `payment_failed`, and `refund`. Grace ends exclusively at `grace_until`; downgrade becomes effective inclusively at `change_effective_at`. Refund revocation and quota/seat blocking are explicit Boolean policies.

Seat events assign or revoke a stable `seat_id`. Usage events carry stable `usage_id`, increasing `version`, nonnegative `units`, and `occurred_at`. Select the greatest accepted version per usage identity. Count occurrence in `[period_start, period_end)` only. Accept receipt through the inclusive `usage_receipt_deadline`. Conflicting identity or usage-version facts raise `ValueError`.

Return entitlement, independent financial/subscription states, seat count/limit/overage, usage total/quota overage, and issues. Compare observed entitlement with the derived policy result; disagreement is `entitlement-mismatch`.

## Bounded shrinking

`shrink_duplicate_cancellation(events, violates)` accepts at most 32 records. Delete irrelevant records while preserving exact event identity and a preceding reservation for each cancellation. Invoke the supplied independent predicate only on legal sequences. Return a deletion-minimal counterexample. Reject illegal or nonfailing inputs. Preserve and replay the explicit minimal sequence in the tests; do not treat invalid shrinks as product failures.
