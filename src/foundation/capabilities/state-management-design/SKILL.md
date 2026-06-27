---
name: state-management-design
description: Classifies server, UI, form, authentication, and cache state and assigns ownership without defaulting to a global store.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "33"
changeforge_version: 0.1.0
---

# Mission

**Design frontend state ownership so that every client-side value has a single authoritative source, a defined lifecycle, a synchronization and invalidation strategy, and a reset or expiry rule** - preventing stale server data from silently drifting from source truth, authentication state from persisting after logout or permission change, optimistic updates from leaving the UI inconsistent on failure, and global state stores from becoming unmanaged dumping grounds for unrelated page concerns.

# When To Use

Use this capability when: a change adds or substantially modifies how data is fetched, cached, or synchronized between the server and client; a form introduces a new draft lifecycle with validation, submission, and reset behavior; authentication or permission state needs to reflect server-side changes such as logout, session expiry, or role change; optimistic updates are being introduced and need rollback semantics; cross-route or cross-feature state coordination is required; or client-side persistence such as localStorage, sessionStorage, IndexedDB, or cookies is being added for state that has privacy or stale-data implications.

# Do Not Use When

Do not use this capability for: server-side session and token management (use `authentication-authorization`); request lifecycle design including retry, error handling, and loading states at the API boundary (use `frontend-api-integration`); form field validation rules and submission behavior as the primary concern (use `form-validation-design`); purely computational derived values with no persistence or synchronization concern.

# Stage Fit

Use during experience-definition, implementation-planning, coding, bug-fix, debugging, code-review, refactoring, testing, release-readiness, and handoff when frontend values need source-of-truth, lifecycle, invalidation, persistence, or reset decisions. In planning, produce the state inventory before choosing storage. In coding/code-review, reject stale project-memory or repository-graph claims unless current source, owners, cache keys, auth paths, and tests confirm the pattern is still valid. During testing, release-readiness, and handoff, reconcile final state claims with validation freshness, browser-session limits, and residual evidence boundaries. Hand off when the primary question is server identity/session design, request lifecycle, form validation, route guards, or executable frontend test strategy.

# Non-Negotiable Rules

- **Classify state before choosing storage.** The classification categories are: server state, UI state, form state, authentication/permission state, persisted client preference, and derived state. Derived state is computed from source state and must not be stored separately unless there is a measured performance reason and an invalidation rule.
- **Server state must define freshness window, stale-while-revalidate behavior, and invalidation triggers.** A React Query, TanStack Query, SWR, Apollo, RTK Query, or Relay entry is cached server state, not local UI state. Define cache key, `staleTime`, `gcTime`/`cacheTime`, mutation invalidations, focus/reconnect revalidation, stale display behavior, and permission/session reset.
- **Authentication and permission state must come from a trusted server-side source.** UI visibility, client-writable storage, or decoded claims without revalidation are not authorization. Auth state must be sourced from a validated session or identity endpoint, invalidated on logout/session expiry/401/role change, and cleared from in-memory stores, query caches, and sensitive browser storage.
- **Global state requires a concrete cross-route or cross-feature justification.** Put state at the lowest owner containing all readers and writers. A global store is justified only when multiple routes or feature areas share the value with consistent synchronization semantics and a named owner.
- **Optimistic updates require explicit rollback on failure.** Capture pre-mutation state, apply the optimistic view, replace it with server-confirmed state on success, revert deterministically on failure, show the user the actual state, and map conflict handling to tests.
- **Client-side persistence of sensitive state requires explicit privacy classification.** Tokens, session identifiers, user identifiers, partial payment data, or sensitive drafts must not be placed in client-writable storage without a security/privacy decision, expiry, clear-on-logout behavior, and XSS exposure review. Prefer httpOnly Secure SameSite cookies for sensitive session tokens.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Server cache ownership | Query cache, generated client, loader data, stale data, mutation invalidation, or background revalidation. | Source of truth, cache key, freshness, invalidation, stale display, auth/session reset. | Current API/client/cache pattern, query keys, mutation list, staleTime/gcTime, invalidation tests. | `frontend-api-integration`, `frontend-testing` | Global store redesign unless needed. |
| Local UI and derived state | Tabs, filters, modals, selected item, computed values, or prop drilling concern. | Lowest owner, reset on unmount/route change, no duplicate derived state, stable memoization. | Readers/writers, route/component owner, reset trigger, derivation source. | `page-component-decomposition`, `interaction-state-modeling` | Cache policy design unless server data exists. |
| Form draft lifecycle | Draft input, autosave, wizard resume, conflict with server data, or navigation away. | Draft owner, validation timing boundary, submit/reset, conflict preservation, sensitive draft persistence. | Form owner, source record, reset/confirm behavior, conflict state, persistence/privacy decision. | `form-validation-design`, `frontend-api-integration` | Server-side validation taxonomy. |
| Auth and permission state | Session expiry, logout, role change, route gating, 401/403, or privileged UI. | Trusted source, revalidation, cache clearing, cross-tab logout, non-client-writable permission state. | Identity endpoint/session source, clear-on-logout checklist, 401 handler, role-change behavior. | `security-privacy-gate`, `authentication-authorization`, `routing-navigation-design` | Route layout design. |
| Optimistic and concurrent mutation | Immediate UI update, reorder/delete/edit, conflict, offline action, or duplicate click. | Pre-mutation snapshot, rollback, conflict resolution, stale server reconciliation, race handling. | Mutation list, previous state capture, rollback trigger, conflict state, test map. | `idempotency-retry-design`, `frontend-api-integration` | Silent retry. |
| Persisted client state | localStorage/sessionStorage/IndexedDB/cookie use, theme/locale, draft resume, or cross-tab sync. | Privacy classification, expiry, clear policy, storage event/BroadcastChannel behavior, per-user keying. | Stored keys, sensitivity class, expiry, clear-on-logout, cross-tab/session behavior. | `security-privacy-gate`, `frontend-testing` | Persisting server truth by default. |

# Industry Benchmarks

Anchor against TanStack Query/React Query, SWR and RFC 5861 stale-while-revalidate, RTK Query and Redux Toolkit selector guidance, Relay/Apollo cache normalization, XState/Zustand/Jotai/Valtio/Pinia/NgRx placement patterns, React external-store and Hooks guidance, OWASP Session Management, secure browser storage guidance, WCAG error-prevention expectations for important form submissions, and browser cross-tab primitives such as `storage` events and `BroadcastChannel`. Keep this body focused on routing, ownership, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed classification, freshness, auth, optimistic rollback, persistence, graph/memory/trajectory, and validation matrices.

# Selection Rules

Select this capability when **frontend state ownership and synchronization is the primary design question**. Route elsewhere when: API request lifecycle, retry, error handling, cancellation, or response validation is primary (use `frontend-api-integration`); form field validation and submission rules are primary (use `form-validation-design`); route-level access guarding is primary (use `routing-navigation-design`); server-side session and token management need design (use `authentication-authorization`); or full interaction status matrices are primary (use `interaction-state-modeling`).

# Proactive Professional Triggers

- **Signal:** Server data is copied into component state, global state, or persisted storage without freshness and invalidation rules. **Hidden risk:** UI drifts from server truth and stale data survives mutations. **Required professional action:** define server-state cache owner and invalidation map. **Route to:** `frontend-api-integration`, `frontend-testing`. **Evidence required:** source query, cache key, mutation invalidations, stale behavior, validation map.
- **Signal:** Authentication or permission state is client-writable, inferred from UI, or stale after logout, 401, session expiry, role change, or cross-tab sign-out. **Hidden risk:** unauthorized UI disclosure, stale protected cache, or shared-device data leak. **Required professional action:** require trusted source, revalidation, cache/storage clearing, and denied-state tests. **Route to:** `security-privacy-gate`, `authentication-authorization`, `routing-navigation-design`. **Evidence required:** identity source, clear-on-logout checklist, 401 handler, cross-tab behavior.
- **Signal:** Optimistic update, offline action, reorder, or delete has no pre-mutation snapshot, rollback, or conflict handling. **Hidden risk:** user sees a state the server rejected. **Required professional action:** require rollback and reconciliation contract. **Route to:** `frontend-api-integration`, `idempotency-retry-design`. **Evidence required:** snapshot, rollback trigger, conflict state, user notification, test.
- **Signal:** A global store is proposed for page-local, transient, or single-consumer values. **Hidden risk:** ownership drift, unnecessary rerenders, stale cross-route state, and hard-to-test coupling. **Required professional action:** push ownership to the lowest component/route or document cross-feature justification. **Route to:** `page-component-decomposition`, `implementation-structure-design`. **Evidence required:** readers, writers, owner, reset/invalidation rule.
- **Signal:** localStorage, sessionStorage, IndexedDB, or cookies are used for tokens, identity, user-specific server data, drafts, or sensitive preferences. **Hidden risk:** XSS exposure, stale cross-user data, privacy over-retention, or compliance issue. **Required professional action:** classify data and define storage, expiry, clear, and redaction rules. **Route to:** `security-privacy-gate`. **Evidence required:** stored keys, sensitivity class, expiry, clear-on-logout, storage threat notes.
- **Signal:** Project memory, repository graph, generated context, or earlier execution trajectory says a store/cache/hook pattern exists. **Hidden risk:** stale pattern copied after framework, auth, cache, or test conventions changed. **Required professional action:** confirm current source before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected pattern, freshness limit, validation command or residual risk.

# Risk Escalation Rules

Escalate when auth or permission state can remain stale after logout or role change and render privileged UI; an optimistic update affects financial, irreversible, inventory, compliance-sensitive, or externally visible data; sensitive user values such as JWTs, session IDs, emails, payment fragments, or regulated data are stored in client-writable storage; cross-tab state synchronization is required for logout or permission refresh; a global store becomes an unowned dumping ground for unrelated pages; or project memory/graph evidence conflicts with current source.

# Critical Details

- **Do not copy server truth into a parallel local state value.** `const [user, setUser] = useState(fetchedUser)` becomes stale unless every source update is mirrored. Keep server data in the server-state cache and derive display values directly; only create a local draft when the user is intentionally editing.
- **Auth state must survive role-change and logout edge cases.** Role revocation, 401, session expiry, and logout in another tab must invalidate protected caches and client-visible permission state. A menu hiding rule is not authorization and a stale admin flag in localStorage is not trusted evidence.
- **Form persistence must be intentional.** Draft state that survives navigation can be a resume feature or a sensitive data leak. Define owner, reset, confirmation, conflict handling, and persistence/privacy behavior before implementation.
- **Derived values should be computed, not stored.** Storing `fullName` alongside `firstName` and `lastName` creates a synchronization obligation. Use selectors, memoization, or state-machine guards unless measured performance requires a stored snapshot.
- **Global state is an architectural decision.** A store introduces subscription, reset, persistence, test, and ownership obligations. If the value has one route or one component owner, default to local ownership.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `const [user, setUser] = useState(apiResponse.user)` | Copy of server data never updates when server changes. | Read from the server-state cache or create an explicit editable draft. |
| `localStorage.setItem('accessToken', jwtToken)` | Token is exposed to same-origin JavaScript and XSS theft. | Prefer httpOnly Secure SameSite cookie and never expose token to JS. |
| Logout clears React state but not query cache | User-specific data can survive sign-out or appear after re-login. | Clear protected caches and user-specific storage on logout/401. |
| Optimistic item stays visible after API failure | UI shows a value rejected by the server. | Capture previous state and rollback on error with user-visible notice. |
| Permission check from localStorage role | Attacker or stale data can alter privileged UI. | Source permission from validated server session/identity endpoint. |
| Global store holds page filters and modal state | Transient values leak across routes and complicate tests. | Keep page-local state in page or component owner and reset on unmount/navigation. |

# Failure Modes

- **Stale copied server truth:** server data copied into component, global, or persisted state shows an old profile, permission, or balance after the query source changes.
- **Logout data leak:** logout clears React state but leaves query cache, persisted draft, subscription, or user-specific storage visible to the next user on a shared device.
- **Revoked-role drift:** permission state is not revalidated after role revocation, 401, or session expiry, so privileged controls remain visible and protected cache entries stay readable.
- **Optimistic delete ghost:** an item is removed before durable server confirmation; the API rejects the delete, rollback is missing, and the user believes an irreversible action succeeded.
- **Token in client-writable storage:** JWT, refresh token, session identifier, or entitlement value in localStorage/sessionStorage is exposed to same-origin JavaScript and XSS theft.
- **Sensitive draft persistence:** payment, health, regulated, or free-text draft state survives navigation, logout, or user switch and later submits stale or wrong data.
- **Global-store dumping ground:** a global store has no owner, so unrelated routes mutate filters, modals, auth-derived flags, or server snapshots and create nondeterministic regressions.
- **Stale graph or memory reuse:** project memory or repository graph points to an old store, query key, persistence helper, or logout pattern after framework, auth, cache, route, or test ownership changed.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 state ownership routing, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete state inventory, cache invalidation map, auth/logout clearing rule, form draft lifecycle, optimistic rollback, persisted client-state decision, or validation map. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, state classification, freshness/auth/persistence matrices, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording changes where the inline output contract and quality gate are enough.

# Output Contract

Return a state ownership map with:

- `mode_selected` (server cache ownership / local UI and derived state / form draft lifecycle / auth and permission state / optimistic and concurrent mutation / persisted client state)
- `state_scope` (surface, route/component/store boundary, user goal, affected values, readers, writers, and reset/invalidation owners)
- `source_evidence` (current source files, store/hooks/cache clients, API contracts, identity/session source, tests/stories, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused store, query key, hook, selector, persistence key, auth handler, or test pattern)
- `state_inventory` (per value: name, classification, source of truth, owner component/store, readers, writers, lifecycle events, reset/expiry rule)
- `server_state_config` (per cached query: cache key, staleTime, gcTime/cacheTime, invalidation triggers, refetch/focus/reconnect behavior, stale display behavior, permission/session reset)
- `auth_state_design` (trusted source, revalidation interval/event, role-change handling, 401 handler, cross-tab logout, cleared-on-logout checklist)
- `form_state_design` (draft ownership, validation/submission boundary, conflict handling, sensitive draft persistence, submit/cancel/navigation reset)
- `optimistic_update_design` (per mutation: pre-mutation snapshot, optimistic application, server confirmation, rollback, conflict resolution, user notification)
- `client_persistence_privacy_model` (per persisted value: storage mechanism, per-user keying, sensitivity class, expiry, clear-on-logout, XSS/privacy exposure)
- `global_state_justifications` (per global value: cross-route or cross-feature consumer evidence, owner, boundary, subscription/reset/performance consideration)
- `derived_state_map` (per derived value: source states, computation, selector/memoization pattern, reason if stored)
- `race_conditions` (concurrent read/write/update risks, cross-tab behavior, stale response risk, resolution strategy)
- `state_to_validation_map` (each state value, cache invalidation, auth branch, persistence rule, rollback, and race condition mapped to validator/test/manual evidence or residual risk)
- `reuse_and_placement_rationale` (why each state owner and storage location is reused, changed, or rejected)
- `handoff_boundaries` (what belongs to API lifecycle, form validation, route guards, server auth/session, security/privacy, interaction states, or frontend testing)
- `validation_evidence` (commands/tests/reviews run, outcome, and what they prove)
- `evidence_limits` (source not inspected, browser behavior not verified, deployed auth/cache behavior not proven, or external framework assumption retained)

# Evidence Contract

Close a state-management-design output only when it names selected mode, boundaries inspected, current source evidence inspected, graph/memory/trajectory reuse judgment, every client-side value classification, source of truth, owner, lifecycle, reset/expiry/invalidation rule, auth and persistence privacy decisions, optimistic rollback and race handling, state-to-validation map, validation commands or report artifacts with exit codes, what evidence proves, what evidence does not prove, validation freshness, handoff boundaries, rollback or reroute note, next gate, residual risk, and evidence limits. A generic "use React Query" or "put it in Zustand" statement is not sufficient evidence.

# Benchmark Coverage

Improved state management plans reject common weak patterns: copied server truth, stale auth after logout, client-writable permissions, unbounded localStorage, global stores for page-local values, stored derived values, optimistic updates without rollback, unowned form drafts, cache invalidation by hope, and stale repository-memory claims. Detailed framework matrices and decision trees belong in references so the main body stays efficient.

# Routing Coverage

Route here when frontend state ownership, source-of-truth selection, cache invalidation, global store justification, persisted client state, auth/permission state, form draft ownership, derived state, or optimistic rollback is primary. Hand off when the primary work is request lifecycle (`frontend-api-integration`), full interaction state feedback (`interaction-state-modeling`), field validation (`form-validation-design`), route guarding (`routing-navigation-design`), server auth/session design (`authentication-authorization`), security/privacy review (`security-privacy-gate`), or executable coverage (`frontend-testing` / `quality-test-gate`).

# Quality Gate

The state design is complete only when:

1. Selected mode, state scope, and current source evidence are explicit.
2. Every state value has classification, source of truth, owner, readers, writers, lifecycle, reset/expiry rule, and validation expectation.
3. Server state has cache key, staleTime, gcTime/cacheTime, invalidation triggers, revalidation behavior, stale display behavior, and session/permission reset.
4. Auth and permission state use a trusted source and define revalidation, 401 handling, role-change behavior, cross-tab logout, and memory/cache/storage clearing.
5. Sensitive or user-identifying persisted state has privacy classification, storage mechanism, expiry, per-user isolation, clear-on-logout rule, and security/privacy handoff when needed.
6. Global state has concrete cross-route or cross-feature consumer evidence, owner, boundary, reset/invalidation behavior, and performance/test impact.
7. Derived values are computed from source state unless storage has measured justification and synchronization rule.
8. Form state has owner, conflict handling, validation/submission boundary, sensitive draft persistence decision, and reset behavior on submit/cancel/navigation/logout.
9. Optimistic updates capture pre-mutation state, confirm durable success, rollback on failure, handle conflicts, and notify users.
10. Race conditions cover concurrent mutations, stale responses, cross-tab changes, route changes, and permission/session transitions.
11. Graph, memory, and execution-trajectory reuse claims are accepted, rejected, or marked not verified with inspected paths and freshness limits.
12. Every state, cache, auth, persistence, rollback, and race decision maps to tests, validators, review evidence, or named residual risk.
13. Handoff boundaries are explicit so state evidence is not over-claimed as server auth, API contract, accessibility, or deployed browser proof.
14. Evidence limits and rollback path are named before handoff.

# Used By

- frontend-change-builder

# Handoff

Hand off to `frontend-api-integration` for request lifecycle, response validation, retry, timeout, cancellation, and API error mapping; `form-validation-design` for field validation rules and submission authority; `authentication-authorization` for server-side identity, sessions, and token controls; `routing-navigation-design` for auth-gated route behavior; `interaction-state-modeling` for user-facing loading/error/empty/disabled state matrices; `security-privacy-gate` for sensitive client persistence, token exposure, privacy, and permission leak review; `frontend-testing` for optimistic update, stale state, auth clearing, persistence, and race-condition coverage.

# Completion Criteria

The capability is complete when **every client-side value has a single authoritative source, a defined lifecycle, an invalidation or reset rule, validation evidence, and no sensitive state leaks across sessions, tabs, users, or client-writable storage without explicit justification and security/privacy review**.
