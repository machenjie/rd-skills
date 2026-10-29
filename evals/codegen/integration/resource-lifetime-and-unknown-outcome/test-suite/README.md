# Test Suite

## Required Checks

Nineteen assertions cover read/cancel/completion/error cleanup, repeated effect cleanup, tenant/locale cache identity, outcome reconciliation, persistent migration, host message identity, lazy-query materialization, selected MCP contract checks, initial hydration, value transfer, and independently authorized server actions.

## Fixtures

`fixtures/passing/subject.py` is the positive control. Ten faulty controls each change one mechanism: premature close, escaped lazy evaluation, selected-version checking, schema binding, token audience, annotation-based permission, business-error classification, initial-versus-later render choice, serialization, or server-action authority. The runnable starter leaves streaming incomplete; its other adapters remain callable.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

The same assertions reject each isolated fault and the incomplete starter. Query construction emits no read; materialization must precede transaction close, and later serialization must add no read. MCP admission failures cannot dispatch writes, and business errors remain distinct from protocol or shape errors. The fixture supports exact integer/string request IDs and matches response IDs by type and value; boolean/number confusion is rejected without asserting this restricted ID domain for all JSON-RPC implementations. Matching post-effect markup cannot conceal a first-render mismatch. These are declared deterministic fixture contracts, not real React, Django, ASGI, MCP negotiation/SDK, browser, database-isolation, or provider behavior.
