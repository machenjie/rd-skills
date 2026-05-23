# Security Checks

## Threat Surface

Order read exposes customer data, tenant membership, shipment addresses, and
support case relationships. The critical failure mode is object authorization
that trusts only the order id.

## Required Checks

- Verify every returned order was scoped to the current actor.
- Verify cross tenant reads fail without revealing the target tenant data.
- Verify inactive support cases do not grant access.
- Verify audit logging avoids addresses, line items, and unnecessary PII.
- Verify denied and missing resources have intentional status semantics.

## Rejection Cases

- Any code path that returns an order loaded by id without policy evaluation.
- Any solution that treats all support agents as globally authorized.
- Any denial response that includes shipment address, line items, or customer email.