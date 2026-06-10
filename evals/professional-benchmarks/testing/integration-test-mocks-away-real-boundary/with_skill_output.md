Selected stage: testing.
Selected professional skill: quality-test-gate.
Selected capabilities: integration-testing.

Hidden risks: integration test mocks away real boundary; mocked repository hides database constraint or transaction behavior; transaction failure path not tested against real database.

Inspected boundaries: service, real database container, transaction boundary, event capture, external billing stub, data setup, cleanup, and rollback assertion.

Evidence required: real integration boundary exercised; environment isolation and cleanup evidence; failure-path rollback validation evidence.

Output obligations covered: integration boundary evidence; validation evidence for success and failure paths; what evidence proves and does not prove; residual external boundary owner.

Validation command: `python3 -m pytest tests/integration/test_account_upgrade.py` (not run in fixture; expected outcome is success path plus billing-failure rollback output).
What evidence proves: the selected service/database/event seam works against realistic infrastructure and rolls back on injected failure.
What evidence does not prove: full browser behavior, production billing provider behavior, or unrelated consumers.

Residual risk: provider sandbox compatibility remains unverified; owner: integration-change-builder.
Next gate: contract-testing for billing provider request/response expectations.
