Review this integration test proposal:

The account upgrade flow writes an account row, emits an event, and must roll
back on billing failure. The proposed "integration" test mocks the repository,
mocks the transaction manager, and stubs the event bus. It asserts only that the
service returned `ok`, with no real database constraint, rollback, event payload,
or cleanup evidence.

Decide whether the test proves the integration boundary and state the evidence
required.
