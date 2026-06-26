# Frontend API Integration Checklist

- Select the integration mode and list current source evidence, including API client, schema, mocks, tests, graph, memory, and trajectory freshness limits.
- List every read and write operation used by the UI.
- Define timeout, cancellation, request identity, current input/cursor binding, and stale response handling.
- Define retry policy per operation class and confirm unsafe mutations require idempotency plus unknown-timeout handling.
- Handle authentication expiry, refresh-once, refresh failure, protected cache clearing, sign-out, and permission changes.
- Map 401, 403, 404, 409, 422, 429, timeout, network, and 5xx responses to frontend states and safe recovery actions.
- Define pagination model, stable ordering, tiebreaker, empty page, filtered empty, and end-of-list behavior.
- Define cache keys, staleTime, gcTime, invalidation triggers, session reset, background refresh, and stale-data presentation.
- Validate response shape before rendering or storing API data.
- Define optimistic update rollback, durable confirmation, conflict behavior, and user-visible failure copy.
- Define telemetry: trace propagation, safe diagnostics, token/PII redaction, and browser destination allowlist when relevant.
- Map each operation, lifecycle state, retry/idempotency rule, auth branch, schema, cache rule, pagination edge, optimistic update, and telemetry rule to a validator/test or residual risk.
- Add tests for timeout, cancellation, stale response, retry dedup, auth expiry, denied state, malformed response, pagination, cache invalidation, optimistic rollback, and error recovery.
- State handoff boundaries and evidence limits so frontend integration evidence is not over-claimed as server contract, deployed auth, real browser, or production third-party proof.
