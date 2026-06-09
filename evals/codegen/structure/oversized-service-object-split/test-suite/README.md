# Test Suite

## Required Checks

- Unit tests for pure cancellation and refund-hold decisions.
- Service-level tests through the public cancellation use case.
- Regression tests for existing deadline, shipment, invoice, and refund behavior.

## Fixtures

Order fixtures must live under the orders test boundary and state the behavior they represent.

## Expected Commands

- `npm test -- orders`
- `npm run lint`

## Regression Cases

- Premium customer inside grace period can cancel.
- Premium customer outside grace period cannot cancel.
- Disputed order receives refund hold.
- Existing shipped order denial remains unchanged.
