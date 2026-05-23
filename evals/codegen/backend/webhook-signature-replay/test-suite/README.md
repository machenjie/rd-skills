# Test Suite

## Required Checks

- Valid signature with current timestamp processes exactly one shipment update.
- Invalid signature rejects before shipment update.
- Same event id delivered twice does not repeat side effects.
- Stale timestamp outside five minutes is rejected.
- Missing signing secret fails closed during request handling or startup validation.

## Fixtures

- Signing secret fixture and helper that computes provider compatible signatures.
- Raw JSON body fixture with stable byte representation.
- Event store fixture that can simulate duplicate insert behavior.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing valid shipment update still works with a correct signature.
- Invalid JSON with a bad signature is rejected as signature failure first.
- Duplicate event response remains safe for provider retries.