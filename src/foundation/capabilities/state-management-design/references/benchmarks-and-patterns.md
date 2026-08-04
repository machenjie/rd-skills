# State Management Benchmarks And Patterns

Load this reference when client state authority, cache lifetime, session reset, persistence, optimistic behavior, or cross-feature ownership changes. Do not load it for a single local value with an obvious owner and reset.

## Decision Checklist

1. **Inventory:** enumerate values hidden in components, hooks, route/search params, query caches, stores, providers, browser storage, workers, and subscriptions—not only named global stores.
2. **Classify:** distinguish server, local UI, form draft, auth/permission, preference, derived, shared/global, and ephemeral operation state before choosing storage.
3. **Source of truth:** name the authoritative writer, readers, trust boundary, lifetime, and conflict rule. For privileged actions, authorize with validated server-side subject and resource state instead of client permission state.
4. **Cache key:** derive response-varying resource, identity, query, projection, and locale dimensions from the response function, with cross-scope and query-shape collision tests.
5. **Freshness:** tie stale/retention/revalidation behavior to domain volatility and user-decision risk; a library default is not evidence.
6. **Invalidation:** name mutations, events, route actions, admin changes, deletes, visibility changes, and dependency recovery that invalidate each cached view.
7. **Auth reset:** on logout, 401/session failure, user or tenant switch, and role change, revoke privileged rendering and clear/revalidate protected memory, cache, storage, subscriptions, and cross-tab state as applicable.
8. **Local versus global:** keep state at the lowest owner; broaden it only for current cross-owner consumers and name reset, subscription, performance, and test contracts.
9. **Derived state:** recompute through selectors/memoization from authoritative inputs; persist a derivative only with an explicit cost, invalidation, and reconciliation need.
10. **Form draft:** define submit, cancel, navigation, validation failure, conflict, logout, and resume behavior while separating editable draft from server truth.
11. **Persistence:** choose URL, cookie, local/session storage, IndexedDB, or no persistence from shareability, lifetime, sensitivity, quota, expiry, schema migration, per-user keying, and clear rules—not convenience.
12. **Optimistic mutation:** snapshot affected views, prevent duplicate intent, reconcile server truth, roll back or expose partial/unknown outcome, and preserve a safe user recovery path.
13. **Concurrency:** define stale response, overlapping mutation, version/etag, reorder, cross-tab, and subscription race behavior; last-write-wins is a decision requiring consequence evidence.
14. **Current convention:** inspect existing query, store, authentication, and persistence helpers before introducing another owner or reset path, with accepted and rejected reuse recorded.
15. **Routes and proof:** send API cancellation/error mapping to `frontend-api-integration`, UI states to `interaction-state-modeling`, forms to `form-validation-design`, identity authority to `authentication-authorization`, sensitive persistence to `security-privacy-gate`, and executable cache/reset/race proof to `frontend-testing`.

## Proof Limits

Unit/component tests do not prove real browser eviction, cross-tab timing, deployed session revocation, provider cache semantics, or production race frequency. Source inspection cannot discover runtime state or unknown consumers. Name untested browsers, identities, offline behavior, persistence migrations, and concurrency schedules.

Reject copied server truth, broad invalidation without cost or rationale, protected caches surviving identity change, and client-writable permissions. Also reject optimistic effects without rollback or unknown-outcome state, indefinite sensitive drafts, and global stores chosen before ownership is known.
