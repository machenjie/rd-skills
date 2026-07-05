# Unit Testing Checklist

- Name the behavior, rule, invariant, calculation, or branch under test.
- Cover success, boundary values, invalid inputs, edge cases, and error paths.
- Control clock, randomness, locale, timezone, and shared state.
- Mock only meaningful boundaries.
- Avoid assertions tied only to private implementation details.
- Ensure the test would fail for a real behavioral regression.
