# Example Output

Affected surfaces: API contract, backend validation, database index, client error handling, docs.

Indirect impact: Existing clients may parse the old error code.

Required gates: `data-api-contract-changer`, `backend-change-builder`, `quality-test-gate`, `delivery-release-gate`, `change-documentation-gate`.

Rollback concern: Migration adds an index that can remain after rollback, but write-path behavior must be flag controlled.
