---
name: state-management-design
description: Classifies server, UI, form, authentication, and cache state and assigns ownership without defaulting to a global store.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "33"
changeforge_version: 0.1.0
---

# Mission

**Design frontend state ownership so that every client-side value has a single authoritative source, a defined lifecycle, a synchronization and invalidation strategy, and a reset or expiry rule** — preventing stale server data from silently drifting from source truth, authentication state from persisting after logout or permission change, optimistic updates from leaving the UI inconsistent on failure, and global state stores from becoming unmanaged dumping grounds for unrelated page concerns.

# When To Use

Use this capability when: a change adds or substantially modifies how data is fetched, cached, or synchronized between the server and client; a form introduces a new draft lifecycle with validation, submission, and reset behavior; authentication or permission state needs to reflect server-side changes (logout, session expiry, role change) in real time; optimistic updates are being introduced and need rollback semantics; cross-route or cross-feature state coordination is required; or client-side persistence (localStorage, sessionStorage, IndexedDB, cookies) is being added for state that has privacy or stale-data implications.

# Do Not Use When

Do not use this capability for: server-side session and token management (use `authentication-authorization`); request lifecycle design including retry, error handling, and loading states at the API boundary (use `frontend-api-integration`); form field validation rules and submission behavior as the primary concern (use `form-validation-design`); purely computational derived values with no persistence or synchronization concern.

# Non-Negotiable Rules

- **Classify state before choosing storage.** The five classification categories are: (1) Server state — data owned by the backend, fetched over the network, cached client-side with freshness and invalidation rules; (2) UI state — transient view state local to a component (open/closed, selected tab, modal visibility); (3) Form state — draft input lifecycle from first keystroke to submission confirmation; (4) Authentication state — identity, session validity, role/permission set sourced from a trusted identity system; (5) Persisted client preference — user preference stored client-side (theme, locale, layout) with explicit expiry and privacy classification. Derived state is computed from one of the above — it must not be stored as a separate value unless there is a demonstrated performance reason.
- **Server state must define freshness window, stale-while-revalidate behavior, and invalidation triggers.** A fetch result stored in React Query / TanStack Query / SWR / Apollo Client is not "local state" — it is a cached server state entry. The cache entry must have: `staleTime` (how long the cached value is considered fresh without refetching), `gcTime`/`cacheTime` (how long to retain after last use), `invalidation triggers` (which mutations or events force a refetch), and `stale data behavior` (show stale data while revalidating, show loading spinner, or block render).
- **Authentication and permission state must come from a trusted server-side source; it must never be inferred from UI visibility alone.** A component that decides "if the user can see the admin menu, they must be an admin" is not performing authorization — it is guessing. Authentication state must be: sourced from a validated session token or identity endpoint; re-validated on route change or on a defined interval; invalidated on logout, session expiry, and unauthorized API response (HTTP 401); and cleared completely from all storage on sign-out (including localStorage, sessionStorage, and in-memory cache entries containing user data).
- **Global state requires a concrete cross-route or cross-feature justification.** Placing state in a global store (Redux, Zustand, Jotai, Pinia, NgRx) when it is used by only one component is an abstraction that adds maintenance cost with no benefit. The rule: state belongs at the lowest level in the component tree that contains all its readers and writers. Global state is justified only when two or more distinct routes or feature areas need to share the same value with consistent synchronization semantics.
- **Optimistic updates require explicit rollback on failure.** An optimistic update that is never rolled back on API failure leaves the UI showing a value the server has rejected. Required: (1) apply the optimistic state immediately on user action; (2) send the API request; (3) on success: replace optimistic state with server-confirmed state; (4) on failure: revert to the pre-mutation value; (5) on failure: display an error that communicates the actual state (not the optimistic state). The rollback must be deterministic — not a full page reload.
- **Client-side persistence of sensitive state requires explicit privacy classification.** Storing a JWT, session token, CSRF token, user email, or partial payment data in localStorage means it is accessible to any JavaScript running on the same origin. For sensitive authentication tokens, prefer httpOnly cookies (inaccessible to JavaScript). For any persisted client preference that could identify a user, document the privacy classification and apply the appropriate expiry and clear-on-logout rule.

# Industry Benchmarks

Anchor against: **TanStack Query (React Query) documentation** — `staleTime` vs. `gcTime`; query invalidation via `queryClient.invalidateQueries`; optimistic updates via `onMutate`/`onError`/`onSettled`; query key design for fine-grained invalidation. **SWR (Vercel)** — stale-while-revalidate strategy (RFC 5861); revalidation on focus, on network reconnect; mutation and bound mutation patterns. **Redux Toolkit** — RTK Query for server state; slice design for UI state; `createSelector` for derived state; `extraReducers` for cross-slice concerns. **XState / Zustand / Jotai / Valtio** — actor model for complex form state; atomic state primitives; fine-grained subscriptions. **React RFC — Hooks rules** — `useState` for local UI state; `useContext` for narrow shared state; external stores for cross-route state. **OWASP — Session Management Cheat Sheet** — httpOnly, Secure, SameSite cookie attributes; session invalidation on logout; storage of sensitive values. **WCAG 2.2 — SC 3.3.4 (Error Prevention)** — form submissions with important transactions must be reversible or confirmation-gated; form state must support undo. **RFC 5861 (HTTP Cache-Control Extensions)** — `stale-while-revalidate` and `stale-if-error` as freshness policy primitives.

### State Classification Decision Matrix

| State Characteristic | Classification | Preferred Storage | Invalidation Rule |
| --- | --- | --- | --- |
| Owned by server; fetched over network | Server state | React Query / SWR / Apollo cache | On mutation; on staleTime expiry; on 401 response |
| Transient view flag (open/closed, hover) | UI state | `useState` in component | On component unmount or user action |
| User input between first key and submission | Form state | `useForm` / `useState` in form | On submit success; on explicit reset; on navigation away (with confirm dialog) |
| User identity, roles, session validity | Auth state | Secure httpOnly cookie (token) + in-memory (decoded claims) | On logout; on 401 from any API; on session expiry timer |
| User preference (theme, locale) | Persisted preference | localStorage with explicit key + expiry | On user change; never on logout (preference is not sensitive) |
| Computed from server data | Derived state | Selector / `useMemo` / `createSelector` | Automatically on source state change; never stored separately |
| Cross-route or cross-feature shared value | Global state | Global store (Redux/Zustand/Pinia) | Explicit invalidation rule required in design document |

### Stale Authentication State Risk Decision Tree

```
Does the component render based on a permission or role check?
  YES → Is the permission sourced from a validated, recently-refreshed server response?
        NO  → RISK: UI shows incorrect permission state; enforce re-validation on route entry
        YES → Safe; define re-validation interval (< 5 min for sensitive permissions)

Did the user log out or was their session invalidated?
  → Is in-memory auth state cleared? YES/NO
  → Is React Query / SWR cache cleared for user-specific queries? YES/NO
  → Is localStorage/sessionStorage cleared for user-identifying keys? YES/NO
  → Is the in-memory auth context reset to unauthenticated state? YES/NO
  All must be YES before the logout is complete.

Did an API call return 401?
  → Trigger auth state invalidation immediately
  → Redirect to login
  → Preserve returnTo for the current route
```

# Selection Rules

Select this capability when **frontend state ownership and synchronization is the primary design question**. Route elsewhere when: API request lifecycle (retry, error handling, loading state) is the primary concern (use `frontend-api-integration`); form field validation and submission rules are the primary concern (use `form-validation-design`); route-level access guarding based on auth state is the primary concern (use `routing-navigation-design`); server-side session and token management need design (use `authentication-authorization`).

# Risk Escalation Rules

Escalate when: auth or permission state can remain stale after logout or role change and a component renders privileged UI based on stale state (security risk — unauthorized UI disclosure); an optimistic update affects a financial, irreversible, or compliance-sensitive value and has no rollback (data integrity risk); sensitive user values (JWT, session ID, partial payment data) are stored in localStorage (OWASP Session Management risk — escalate to `security-privacy-gate`); cross-tab state synchronization is required for auth state and the synchronization mechanism is undefined (logout in one tab must not leave another tab with valid session); or a global state store is being used for 20+ values with no ownership boundary (maintainability and performance risk).

# Critical Details

- **The most common server state mistake: copying server data into `useState` and forgetting to sync.** `const [user, setUser] = useState(fetchedUser)` copies the server value into a local state variable. When the server value changes, the local copy is not updated. The correct pattern: keep server data in the server state cache (React Query/SWR), read directly from the cache in components, and never copy it to a parallel `useState`. The only exception is when the component needs to display a locally-edited draft before submitting.
- **Global auth context must handle the "permission changed while user is logged in" case.** If a user's role is changed by an admin while the user's session is active, the user's in-memory permission state will show the old role until the next page load or re-validation. For sensitive role transitions (e.g., admin access revoked), implement a polling mechanism or server-sent event that forces re-validation on role change.
- **Form state that persists across navigation without user intent is a UX defect.** If a user starts filling out a multi-step form, navigates away accidentally, and returns to find the form pre-filled with their previous input — that is either a desirable feature (requires explicit "resume draft" UX) or an unexpected leakage of state (requires explicit reset on navigation away). The behavior must be explicit in the design.
- **Derived state must not be stored as separate state.** `const [fullName, setFullName] = useState(firstName + ' ' + lastName)` creates a synchronization problem: if `firstName` changes, `fullName` is stale until explicitly updated. Derived values must be computed: `const fullName = useMemo(() => firstName + ' ' + lastName, [firstName, lastName])`.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `const [user, setUser] = useState(apiResponse.user)` | Copy of server data never updated when server changes; stale display | Use React Query: `const { data: user } = useQuery(['user', userId], fetchUser)` |
| `localStorage.setItem('accessToken', jwtToken)` | Token accessible to all JS on same origin; XSS can steal token | Use httpOnly Secure SameSite=Strict cookie; token never accessible to JavaScript |
| Logout clears React state but not React Query cache | After logout, another user's data returned from query cache on re-login as same user | `queryClient.clear()` on logout; per-user query keys |
| Optimistic UI with no rollback: list item added, API fails, item stays visible | User sees item that does not exist on server; stale UI; confusion | `onError` in mutation: `queryClient.setQueryData(['items'], previousItems)` |
| Permission check: `if (userState.isAdmin)` where `userState` is from localStorage | Attacker modifies localStorage value; UI renders admin features | Permission sourced from validated server session only; not from client-writable storage |
| Global store holds every page's transient filter/sort state | Filters from Page A appear on Page B after navigation; unexpected behavior | Filter/sort state is local to the page component; cleared on unmount |

# Failure Modes

- Server data copied to `useState`: user profile shows stale name for 20 minutes after update.
- Auth state not cleared on logout: next user on shared computer sees previous user's dashboard.
- Permission state not re-validated after role change: revoked admin user continues to see admin UI for the duration of their session.
- Optimistic update without rollback: user "deletes" a record; delete API fails; record appears gone in UI but still exists on server; user cannot re-interact with it.
- JWT stored in localStorage: XSS attack extracts token; account takeover.
- Stale form draft pre-fills sensitive form on return visit: user submits outdated payment details.

# Output Contract

Return a state ownership map with:

- `state_inventory` (per value: name, classification, source of truth, owner component/store, readers, writers, lifecycle events)
- `server_state_config` (per cached query: staleTime, gcTime, invalidation triggers, stale data behavior)
- `auth_state_design` (source, re-validation interval, cleared-on-logout checklist, 401 handler)
- `form_state_design` (draft ownership, validation timing, reset triggers, submit lifecycle)
- `optimistic_update_design` (per mutation: apply optimistic state, confirm on success, rollback on failure)
- `persistence_decisions` (per persisted value: storage mechanism, expiry, privacy classification, clear-on-logout rule)
- `global_state_justifications` (per global value: cross-route use case, boundary)
- `derived_state_map` (per derived value: source states, computation, `useMemo`/`createSelector` pattern)
- `race_conditions` (concurrent update risks; resolution strategy)

# Quality Gate

The state design is complete only when:

1. Every state value has a classification, source of truth, owner, and lifecycle.
2. All server state has staleTime, invalidation triggers, and stale-data behavior.
3. Auth state has re-validation interval, 401 handler, and logout-clearing checklist.
4. All optimistic updates have rollback on failure.
5. Sensitive values in client storage are documented with privacy classification.
6. Global state has a concrete cross-route justification.
7. No derived values are stored as separate state.
8. Form state has explicit reset behavior on navigation and submit success.
9. Auth state cleared-on-logout checklist covers memory, cache, and storage.
10. Race conditions for concurrent updates have a resolution strategy.

# Used By

- frontend-change-builder

# Handoff

Hand off to `frontend-api-integration` for request lifecycle and error handling; `form-validation-design` for field validation rules; `authentication-authorization` for server-side identity and session management; `routing-navigation-design` for auth-gated route behavior; `frontend-testing` for optimistic update, stale state, and race condition coverage.

# Completion Criteria

The capability is complete when **every client-side value has a single authoritative source, a defined lifecycle, an invalidation or reset rule, and no sensitive state leaks across user sessions or persists in client-writable storage without explicit justification**.
