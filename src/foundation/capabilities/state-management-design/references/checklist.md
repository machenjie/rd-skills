# State Management Design Checklist

- Classify every state value as server, UI, form, authentication, cache, derived, or persisted preference.
- Identify the source of truth for each state value.
- Assign owner, readers, writers, and reset behavior.
- Keep local UI state local unless a broader lifecycle is required.
- Define server-state freshness, invalidation, refetch, and stale display behavior.
- Define form draft lifecycle, conflict handling, and submit reset behavior.
- Define auth expiry, sign-out, role change, and permission refresh behavior.
- Avoid duplicating derived state unless justified.
- Document optimistic updates, rollback, and conflict handling.
- Add tests for synchronization, stale data, and permission-sensitive state changes.
