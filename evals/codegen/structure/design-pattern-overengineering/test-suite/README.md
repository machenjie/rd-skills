# Test Suite

## Required Checks

- Eligible and ineligible discount behavior is covered through the public module.
- Static review rejects strategy with one implementation.
- Static review rejects factory hiding simple constructor behavior.
- Static review rejects abstract base class for reuse and public interface with no current consumer.

## Fixtures

- Order that meets the threshold.
- Order that misses the threshold.
- Existing discount configuration with one rule.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Strategy with one implementation must fail review.
- Factory hiding simple constructor must fail review.
- Abstract base class for reuse must fail review.
- Public interface with no current consumer must fail review.
