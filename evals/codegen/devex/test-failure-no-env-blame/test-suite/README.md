# Test Suite

## Required Checks

- Integration test setup reads the intended test database configuration.
- The repository path is exercised against the configured integration fixture.
- The failure diagnosis records a verified cause and counter-evidence.
- The final validation output is included in completion evidence.

## Fixtures

- Test database config with expected host, port, database, and schema values.
- Order fixture seeded through the integration setup path.
- Failing connection output showing the original symptom.

## Expected Commands

Run `bash ../test-suite/run.sh` from the starter repo.

## Regression Cases

- Skipping the integration fixture should fail review.
- Hardcoding a developer-specific database URL should fail review.
- Environment blame without inspected evidence should fail execution discipline review.