# Reservation, Fulfillment, and Return Transitions

Load for finite-resource allocation, reservation expiry, fulfillment, cancellation, or returns.
Skip catalog display and payment-only integration without resource-state changes.

## Decision Rules

- Name the resource unit, authoritative quantity, reservation owner, and location or channel scope.
- Define the conservation equation using the product states, including unavailable or retired resources.
- Bind a stable identity to each reservation, allocation, fulfillment, cancellation, or product return.
- Choose the transition that owns resource release and prevent duplicate release from retries.
- Resolve confirmation against expiry atomically or through the existing authority and reconciliation mechanism.
- Apply the defined late-payment policy after a reservation expires; payment alone cannot reclaim sold capacity.
- Snapshot accepted price and promotion terms before later catalog changes can rewrite the order.
- Track quantity and state per order line for split orders and partial fulfillment.
- Link each partial return to fulfilled quantity and its eligibility for resale.
- Reconcile transfers and fulfillment across warehouses, locations, or channels without counting stock twice.
- Keep financial settlement, order acceptance, and physical fulfillment independently observable.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Cancel is delivered twice | Available quantity increases at most once for the same release |
| Expiry completes before payment confirmation | Late-payment policy decides refund, reacquisition, or another accepted outcome |
| Only part of a line is returned | Return quantity cannot exceed the fulfilled and unreturned amount |
| Returned item is damaged | Accounting return does not automatically make it available for resale |
| Payment completes before fulfillment | Order remains distinguishable from delivered completion |
| Two channels contend for final capacity | Conservation holds at the authoritative allocation boundary |

## Proof Limits

- Product contracts define expiry, refund, return eligibility, and commercial exceptions.
