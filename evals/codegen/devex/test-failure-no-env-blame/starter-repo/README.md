# Starter Repo

## Stack

Node.js backend integration test harness using a local database fixture and a
small configuration loader.

## Initial State

The integration test fails with a database connection refusal. The repo has a
test database config, setup script, and fixture loader, but one configuration
path is wrong or missing. The failure can be diagnosed without guessing about
the user's machine.

## Files

- `src/config/testDatabase.ts` loads integration-test database settings.
- `test/setupIntegrationDb.ts` starts or validates the fixture database.
- `test/orders.integration.test.ts` exercises the real repository path.
- `package.json` defines the integration test command.

## Constraints

Keep the test as an integration test. Do not replace the repository or database
path with mocks. Diagnose from files, command output, and fixture behavior.