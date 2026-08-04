# Starter Repo

## Stack

Python integration-test reproduction using only stdlib-readable configuration,
fixture, harness, and log files.

## Initial State

The supplied log records a connection refusal before the test body. The
repository-owned configured and expected ports disagree, so the cause can be
verified without guessing about the user's machine.

## Files

- `db_config.py` declares the database host, port, and name.
- `fixtures.py` declares the fixture's expected postgres port.
- `integration_harness.py` compares the config and fixture before the test body.
- `integration.log` records the exact observed setup values and refusal.

## Constraints

Keep the workspace unchanged. Diagnose from the supplied files, cite their
existing lines and values, and describe only a future repair plus validation
plan. Do not apply a fix, invent execution evidence, or include raw command output.
