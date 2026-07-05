# Test Suite

## Required Checks

- Public behavior tests exercise `QuoteService.price_quote()` for ordinary, expired, and tier-dependent quotes.
- External customer tier behavior is represented by a fake or contract seam, not by private helper mocks.
- Private helper export and private call order assertions are rejected.
- Clock, randomness, UUID, file, environment, and HTTP behavior are deterministic.

## Fixtures

Quote fixtures belong under the billing test boundary and must state which pricing rule, tier, or expiration case they represent.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing discount amounts are preserved by characterization tests.
- Private helper export is removed or left inaccessible.
- Fixture ownership is documented when a fixture is shared.
- Flaky clock-dependent tests are replaced with deterministic clock seams.
