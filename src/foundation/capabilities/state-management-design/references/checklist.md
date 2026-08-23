# State Management Design Checklist

- Select the mode: server cache ownership, local UI/derived state, form draft lifecycle, auth/permission state, optimistic/concurrent mutation, or persisted client state.
- When a changed flow introduces or moves client-side state, classify affected values as server, UI, form, authentication/permission, persisted preference, derived, or ephemeral operation state. Resolve ownership or authority ambiguity before choosing storage.
- Identify the authoritative source of truth for each value before choosing storage.
- Assign owner, readers, writers, lifecycle events, reset behavior, expiry, and validation expectation.
- Confirm repository inspection and prior task evidence against current source before reusing stores, hooks, query keys, persistence helpers, or auth handlers.
- Keep local UI state local unless a broader lifecycle is required and justified.
- Define server-state cache key, freshness, invalidation, refetch, stale display, and session/permission reset behavior.
- Define form draft lifecycle, conflict handling, submit/cancel/navigation/logout reset behavior, and sensitive draft persistence policy.
- Define auth expiry, sign-out, 401, role change, permission refresh, cross-tab logout, and protected cache/storage clearing.
- Avoid duplicating derived state unless measured performance justifies storage and synchronization.
- Document optimistic updates, pre-mutation snapshot, durable confirmation, rollback, conflict handling, and user notification.
- For each persisted browser value, record privacy sensitivity, storage mechanism, per-user or per-tenant keying, expiry, and logout or role-change clearing. Avoid unnecessary persistence; test applicable user-switch and cross-tab paths.
- Justify global state with cross-route or cross-feature consumers, owner, boundary, reset/invalidation rule, and test impact.
- Map state, cache, auth, persistence, rollback, race, and global-store decisions to tests, validators, manual review, or residual risk.
- Name handoff boundaries, validation evidence, evidence limits, and rollback path before completion.

## Anti-Patterns

- Promote state globally because prop flow is inconvenient, or duplicate server state without an invalidation owner.
- Key cache or persisted state without tenant, account, resource, or query identity needed to prevent cross-context reuse.
- Let a stale response, optimistic failure, logout, or navigation leave durable or sensitive state under the wrong owner.
