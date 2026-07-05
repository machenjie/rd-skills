# State Management Benchmarks And Patterns

Use this reference when `state-management-design` needs detailed benchmark anchors, decision matrices, or graph/memory/execution coupling beyond the inline `SKILL.md` body.

## Benchmark Anchors

| Benchmark or pattern | State-management implication | Evidence to require |
| --- | --- | --- |
| TanStack Query / React Query | Server state belongs in query cache with query keys, `staleTime`, `gcTime`, invalidation, optimistic `onMutate`/`onError`/`onSettled`, and cache clearing on session change. | Query key, freshness, invalidation, rollback, protected-cache reset. |
| SWR and RFC 5861 | Stale-while-revalidate allows old data to display while refresh runs, but the stale state must be visible when user decisions depend on freshness. | Revalidation trigger, stale display behavior, focus/reconnect policy. |
| RTK Query / Redux Toolkit | Server state should use RTK Query instead of hand-written slices; local UI slices need ownership boundaries; derived data should use selectors. | Slice boundary, selector source, invalidation tags, no duplicated server truth. |
| Relay / Apollo normalized cache | Entity identity, cache normalization, and mutation updates must keep references consistent across screens. | Entity keying, mutation cache updates, eviction/reset rules. |
| XState / state machines | Complex form, wizard, auth, or optimistic flows benefit from explicit states and allowed transitions. | State chart, valid transitions, impossible states excluded. |
| Zustand / Jotai / Valtio / Pinia / NgRx | Global and atom stores are valid only when ownership and cross-feature consumers are explicit. | Store owner, consumers, reset behavior, subscription/performance risk. |
| React Hooks and external store guidance | `useState` is local; `useContext` should stay narrow; external stores must expose consistent snapshots and avoid tearing. | Component owner, context boundary, external-store reason. |
| OWASP Session Management | Sensitive tokens should not be exposed to JavaScript; sessions need invalidation and secure cookie attributes. | Token location, clear-on-logout, 401 handler, XSS exposure review. |
| Browser storage primitives | localStorage/sessionStorage/IndexedDB/cookies differ in lifetime, scope, quota, and JavaScript exposure. | Storage choice, expiry, per-user key, clear rule, cross-tab behavior. |
| WCAG error prevention | Important form submissions should prevent irreversible mistakes with review, confirmation, reversal, or correction. | Draft preservation, submit confirmation, rollback/undo, error recovery. |

## State Classification Decision Matrix

| State characteristic | Classification | Preferred owner/storage | Invalidation or reset rule |
| --- | --- | --- | --- |
| Owned by backend and fetched over network | Server state | TanStack Query, SWR, Apollo, Relay, RTK Query, route loader cache | Mutation invalidation, staleTime expiry, focus/reconnect refresh, 401/session reset. |
| Transient view flag such as tab, modal, hover, popover, expanded row | UI state | Lowest component or route owner with all readers/writers | User action, route change, unmount, explicit reset. |
| User input between first edit and submit | Form state | Form library, reducer, state machine, or form component owner | Submit success, cancel, navigation confirmation, logout, server-conflict resolution. |
| Identity, role, permission, feature entitlement, session validity | Auth/permission state | Trusted identity/session endpoint plus protected in-memory view model | Logout, 401, session expiry, role-change event/poll, cross-tab logout. |
| User preference such as theme, locale, density, column order | Persisted preference | localStorage/IndexedDB/cookie only after privacy and expiry decision | User change, schema version migration, expiry, optional logout rule by sensitivity. |
| Computed display value or aggregate | Derived state | Selector, memoization, computed property | Recomputed from source state; do not persist unless justified. |
| Multiple feature areas coordinate one value | Global/shared state | Explicit store, context, external store, or state machine | Owner-defined reset, invalidation, subscription, and test contract. |
| Browser-only ephemeral resource such as upload progress | Ephemeral operational state | Component, hook, or operation controller | Operation completion, cancel, timeout, navigation cleanup. |

## Server-State Freshness And Invalidation Matrix

| Decision | Required question | Strong answer | Weak answer to reject |
| --- | --- | --- | --- |
| Cache key | What uniquely identifies this data? | Includes resource id, tenant/user scope when needed, filters, sorting, pagination cursor, locale when response changes. | Generic key such as `items` for tenant/user/filter-specific data. |
| Freshness | How long is cached data safe? | `staleTime` tied to domain volatility and user decision risk. | Default freshness accepted without reasoning. |
| Retention | How long after last use can data remain? | `gcTime`/`cacheTime` bounded and privacy-aware. | Protected data retained indefinitely. |
| Invalidation | Which changes make data stale? | Mutation, websocket/SSE event, route action, admin update, logout/401/role change. | "Refresh page" or "eventually updates". |
| Stale display | What does the user see during revalidation? | Stale badge, background spinner, blocking reload, or disabled risky action based on decision risk. | Silent stale display for permission or financial decisions. |
| Error fallback | What if revalidation fails? | `stale-if-error` only when safe; show warning and recovery. | Treat stale data as confirmed success. |
| Session reset | What happens on logout/401/user switch? | Clear protected caches and per-user keys; recompute auth/permission state. | Leave query cache intact across users. |

## Auth, Permission, And Session State Matrix

| Scenario | Required behavior | Validation evidence |
| --- | --- | --- |
| Initial route entry | Load or validate current identity/permission from trusted source. | Route/session source inspected; protected UI waits for source or denied state. |
| 401 from any protected API | Invalidate auth state, clear protected caches, stop privileged rendering, and redirect or reauthenticate. | Test or review showing 401 branch clears memory/cache/storage. |
| 403/permission denied | Render denied state without leaking sensitive resource details. | Error mapping and non-leaking UI copy. |
| Logout | Clear in-memory auth, query/cache entries, user-specific storage, subscriptions, and cross-tab state. | Clear-on-logout checklist and cross-tab event test. |
| Role changed during active session | Revalidate on route, interval, event, or next protected action; revoke privileged UI promptly. | Role-change scenario and freshness limit. |
| Shared device or user switch | Per-user cache/storage keys or full protected data purge. | User switch test or manual evidence. |
| Cross-tab logout | storage event, BroadcastChannel, service worker message, or session endpoint polling. | Cross-tab branch and browser validation or residual risk. |

### Stale Authentication State Risk Decision Tree

```text
Does the component render privileged UI based on identity, role, permission, or entitlement?
  NO  -> Treat as normal UI/server state.
  YES -> Is the value sourced from a validated session/identity endpoint?
          NO  -> Block or route to security/privacy; client-writable permission is unsafe.
          YES -> Is freshness defined for route entry, role change, 401, and logout?
                  NO  -> Require revalidation and clear-on-logout design.
                  YES -> Does logout clear memory, protected cache, and sensitive storage in every tab?
                          NO  -> Require clear checklist and cross-tab synchronization.
                          YES -> State model is acceptable pending validation evidence.
```

## Optimistic Update And Rollback Matrix

| Mutation type | Pre-mutation snapshot | Success reconciliation | Failure rollback | Extra risk |
| --- | --- | --- | --- | --- |
| Toggle or like | Previous field value and affected list/detail cache. | Replace with server-confirmed value. | Restore previous value and show recoverable error. | Duplicate clicks and stale counts. |
| Create item | Temporary id and insertion position. | Swap temp id for server id; refetch affected lists if ordering matters. | Remove temp item and preserve draft if useful. | Duplicate create on retry; use idempotency when needed. |
| Edit item | Previous entity fields and version/etag if available. | Merge server response and invalidate related views. | Restore previous fields or show conflict resolution. | Last-write-wins conflict. |
| Delete item | Previous entity and list position. | Evict after durable confirmation. | Restore entity and position. | Irreversible or compliance data needs confirmation. |
| Reorder | Previous ordered list and version. | Apply server canonical order. | Restore previous order and explain failure. | Concurrent reorder conflicts. |
| Bulk action | Per-item previous state and partial failure map. | Confirm completed items and retry/recover failed subset. | Do not rollback successes unless server contract says atomic. | Partial completion and user confusion. |

## Client Persistence And Privacy Matrix

| Stored value | Default decision | Required controls if persisted |
| --- | --- | --- |
| Access token, refresh token, session id | Do not store in localStorage/sessionStorage. Prefer httpOnly Secure SameSite cookie. | Security/privacy review, XSS exposure note, expiry, rotation, clear-on-logout. |
| Permission or role | Do not trust client-writable storage. | Treat as display cache only; revalidate from server before privileged decisions. |
| User profile/server data | Avoid persistent browser storage unless offline/product requirement exists. | Per-user key, version, expiry, encryption-at-rest decision if available, purge on logout/user switch. |
| Sensitive form draft | Do not persist by default. | Explicit resume UX, expiry, clear-on-submit/logout, privacy classification, user consent if needed. |
| Theme/locale/density | Persist when useful. | Stable key, schema version, fallback default, optional cross-tab sync. |
| Table filters/sort | Prefer URL state for shareable views or page-local state for transient filters. | Reset behavior, route compatibility, no sensitive query values in URL if privacy-sensitive. |
| Feature flags/entitlements | Do not persist as authority. | Client cache only; server/source refresh and safe defaults. |

## Global State Placement Decision Tree

```text
Is there more than one reader or writer?
  NO -> Keep local.
  YES -> Are all readers/writers inside one route or feature boundary?
          YES -> Place at the nearest route/feature owner.
          NO  -> Is the value server-owned?
                  YES -> Use server-state cache, not app store.
                  NO  -> Does it need cross-route consistency or cross-tab persistence?
                          NO  -> Reconsider route-local ownership.
                          YES -> Use a named global store/context/state machine with owner, reset, tests.
```

## Graph, Memory, And Execution Coupling

| Evidence source | How to use it | Failure to avoid |
| --- | --- | --- |
| Repository graph | Identify existing stores, query clients, hooks, auth providers, route owners, persistence helpers, and tests. | Introducing a second store/cache/helper that bypasses local conventions. |
| Project memory | Use prior decisions only as leads; confirm against current source. | Treating stale memory as proof of current architecture. |
| Execution trajectory | Reuse failed-test output, prior validation, or earlier analysis only with freshness limits. | Repeating the same failing path or claiming old validation still proves new behavior. |
| Callers and registry | Confirm which professional skills and capabilities route here and what they expect in the output contract. | Narrow output that fails downstream `frontend-change-builder` or `frontend-testing` handoff. |
| High-scoring sibling patterns | Reuse Stage Fit, Mode Matrix, Evidence Contract, Reference Loading Policy, and validation map structure. | Copying domain-specific content that belongs to API lifecycle or interaction-state modeling. |

## State-To-Validation Matrix

| State decision | Preferred validation |
| --- | --- |
| Server-state invalidation | Unit/integration test for mutation invalidating affected cache keys; manual review of query keys. |
| Stale display behavior | Component/story test showing stale indicator or blocked risky action while revalidating. |
| Logout clearing | Test or manual proof that memory, cache, user-specific storage, and cross-tab state are cleared. |
| 401 handling | API mock test showing auth invalidation and redirect/reauth path. |
| Role-change permission refresh | Test, polling/event review, or explicit residual risk with freshness interval. |
| Form draft reset | Test for submit success, cancel, navigation, conflict, and logout where relevant. |
| Sensitive draft persistence | Privacy/security review plus expiry and clear behavior test. |
| Optimistic rollback | Mutation failure test restoring previous state and showing user-visible error. |
| Concurrent mutation race | Test or state-machine proof for conflict ordering, version/etag, or last-write rule. |
| Global store boundary | Store-level tests for reset, subscriptions, and no cross-route leakage. |
| Derived state | Unit test or review showing derivation recomputes from source and is not stored separately. |

## Review Checklist

1. Inventory every client-side value, not only named stores.
2. Classify each value before selecting storage.
3. Name the authoritative source and owner.
4. Prove existing repository patterns before reusing them.
5. Define server-state cache key, freshness, invalidation, stale display, and session reset.
6. Define auth revalidation, logout, 401, role-change, and cross-tab behavior.
7. Keep local UI state local unless broader lifetime is required.
8. Explain every global-store value with cross-route/cross-feature consumer evidence.
9. Avoid storing derived values; use selectors or memoization.
10. Define form draft reset, conflict handling, and persistence/privacy behavior.
11. Require optimistic rollback and conflict handling for every optimistic mutation.
12. Classify persisted browser values by privacy sensitivity and expiry.
13. Map each state decision to tests, validators, manual review, or residual risk.
14. Name handoffs and evidence limits before completion.

## Anti-Pattern Review

| Anti-pattern | Review response |
| --- | --- |
| "Use Zustand for the page state" | Ask for cross-route consumers and why route-local state is insufficient. |
| "Cache user data in localStorage for speed" | Require privacy classification, stale invalidation, per-user keys, and clear-on-logout; prefer query cache. |
| "Show admin controls if `isAdmin` in localStorage" | Reject; permission must come from trusted server/session source. |
| "Copy query data into component state" | Allow only for editable draft; otherwise read from cache/selector. |
| "Invalidate everything after mutation" | Accept as temporary but require scoped invalidation or rationale for cost. |
| "Optimistic delete then refetch later" | Require snapshot, rollback, and durable confirmation behavior. |
| "Persist draft forever" | Require explicit resume UX, expiry, privacy classification, and clear behavior. |
| "Tests cover happy path" | Require stale, logout, rollback, race, and persistence edge coverage or residual risk. |

## Handoff Boundaries

- `frontend-api-integration`: request cancellation, timeout, retry, response validation, API error mapping, and operation lifecycle.
- `interaction-state-modeling`: user-facing loading, empty, error, disabled, partial, timeout, and accessibility state matrix.
- `form-validation-design`: field-level validation timing, server validation mapping, duplicate-submit rules, and submission authority.
- `routing-navigation-design`: route guards, redirect loops, return-to behavior, route-level auth decisions.
- `authentication-authorization`: server-side identity, token, session, object permission, and trust model.
- `security-privacy-gate`: token storage, client-writable permissions, XSS exposure, privacy classification, sensitive persistence, and audit evidence.
- `frontend-testing`: executable proof for cache invalidation, auth clearing, rollback, persistence, cross-tab, and race conditions.
