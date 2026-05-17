# Frontend API Integration Checklist

- List every read and write operation used by the UI.
- Define timeout, cancellation, and stale response handling.
- Define retry policy and confirm unsafe mutations require idempotency.
- Handle authentication expiry, refresh failure, sign-out, and permission changes.
- Define pagination model, stable ordering, empty page, and end-of-list behavior.
- Define cache keys, invalidation triggers, refresh, and stale-data presentation.
- Validate response shape before rendering or storing API data.
- Map API errors to user-safe messages, retry options, and diagnostics.
- Define optimistic update rollback and conflict behavior.
- Add tests for timeout, cancellation, auth expiry, pagination, stale data, and errors.
