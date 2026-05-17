---
name: interaction-state-modeling
description: Models loading, empty, error, success, disabled, partial, timeout, permission-denied, and related interaction states for user-facing behavior.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "10"
changeforge_version: 0.1.0
---

# Mission

Define a **complete, explicit state matrix for every user-facing interaction** — covering loading, empty, error, success, disabled, partial, timeout, optimistic, and permission-denied states — so users receive accurate feedback at every moment, screen readers receive correct announcements, and systems safely handle incomplete or failed conditions without silent data loss or misleading success indicators.

# When To Use

Use this capability when a change includes: asynchronous data fetching (API calls, GraphQL queries); form submission with server round-trip; actions that may be pending, disabled, or restricted by permission; paginated or infinite-scroll content; optimistic updates that may roll back; background jobs whose progress must be reflected in UI; multi-step wizards with partial completion; or any feature where the user needs to know "what is happening right now and what can I do about it."

# Do Not Use When

Do not use this capability to specify visual design details (color, spacing, typography) — that belongs in `design-system-rules`. Do not use it as a substitute for backend error semantics — if the backend error contract is undefined, use `error-code-design` first. Do not skip this capability because the "happy path is the only expected path" — the happy path is a special case of the state model, and omitting failure states creates unhandled conditions in production.

# Non-Negotiable Rules

- **Every async operation must have at minimum 4 states: idle, loading, success, error.** A two-state model (loading / done) is insufficient; it conflates success and error, and it has no idle baseline.
- **Empty state is not error state.** "No items found" (empty — data exists but query returns zero results) is different from "Failed to load" (error — network or server failure) and different from "You don't have access" (permission-denied — authorization failure). These must produce different UI treatments and different user actions.
- **Disabled actions must be reachable and explainable.** A button that is disabled because the user lacks permission or because a prerequisite is not met must: remain keyboard-focusable (not `disabled` attribute which removes focus); have an accessible tooltip or adjacent description explaining why it is disabled (WCAG 1.3.1 — Info and Relationships). A disabled button with no explanation violates heuristic 1 (visibility of system status).
- **Optimistic update rollback is mandatory when the server can reject the action.** If a UI applies an optimistic update (e.g., like button, reorder, delete) and the server returns an error, the UI must revert to the previous state and display an error message. Silent rollback (revert with no message) leaves the user confused. Visible rollback + error is required.
- **Timeout state must not imply cancellation unless confirmed.** "Request timed out" does not mean the server did not process the request — it may have committed but the response was lost. The timeout state message must reflect uncertainty: "This is taking longer than expected. The action may have completed — you can refresh to check." Never say "Action cancelled" when the server outcome is unknown.
- **State changes must be announced to assistive technology.** Loading indicators must use `aria-live="polite"` or `aria-live="assertive"` (for critical status) with descriptive text. Success and error messages injected into the DOM must use ARIA live regions or `role="alert"` so screen readers announce them (WCAG 4.1.3 — Status Messages, Level AA).
- **Frontend state must align with backend status semantics.** A frontend "success" state that shows before the server confirms durable commit is misleading. Match frontend state transitions to the actual HTTP response status and response body contract.

# Industry Benchmarks

Anchor against: **Nielsen's 10 Usability Heuristics** (1994) — Heuristic 1: Visibility of system status; every state change must keep the user informed; Heuristic 5: Error prevention; Heuristic 9: Help users recognize, diagnose, and recover from errors. **WCAG 2.1 / 2.2** — 4.1.3 Status Messages (Level AA): status messages programmatically determinable via `role` or `aria-live` without receiving focus; 1.3.1 Info and Relationships; 2.1.1 Keyboard (all functionality via keyboard). **XState** (stately.ai/xstate) — JavaScript/TypeScript finite state machine library; makes states and transitions explicit; prevents "impossible states" by modeling only valid transitions; widely adopted for UI state machines. **TanStack Query (React Query)** — `status: 'pending' | 'error' | 'success'`; `fetchStatus: 'fetching' | 'paused' | 'idle'`; `isStale`; built-in background refetch; error retry; exact 4-state model that defines this standard. **SWR** (Vercel) — `{ data, error, isLoading, isValidating }`; stale-while-revalidate; background update state. **Remix `useNavigation` / `useFetcher`** — `state: 'idle' | 'submitting' | 'loading'`; optimistic UI via `useOptimistic`. **Skeleton loading pattern** — placeholder shapes matching expected content layout; reduces perceived loading time; preferable to spinners for content-heavy sections. **Skeleton vs Spinner decision** (NN/g): skeleton for layout-defining content (pages, cards, tables); spinner for actions (button submit, file upload). **Luke Wroblewski "Web Form Design"** — inline validation timing, error state at field level, success state at field level, disabled state with affordance. **ARIA authoring practices** (`aria-busy="true"` on container during load; `aria-live="polite"` for non-critical status; `role="alert"` for critical errors injected into DOM).

### Complete State Matrix

| State | Trigger | User-visible treatment | ARIA / Accessibility | Allowed actions | Recovery |
| --- | --- | --- | --- | --- | --- |
| Idle | Page load, reset | Default content or empty prompt | None required | All available actions | N/A |
| Loading | API call initiated | Skeleton or spinner; disable submit | `aria-busy="true"` on container; `aria-label="Loading..."` | Cancel (if AbortController); navigation | Retry or cancel |
| Success | 2xx response received | Content rendered; transient success toast | `aria-live="polite"` on status region | All actions | N/A |
| Error | 4xx/5xx or network error | Error message with retry CTA | `role="alert"` or `aria-live="assertive"` | Retry; dismiss; contact support | Retry; fix input |
| Empty | 2xx with zero results | Empty state illustration + CTA | Visible text; no special ARIA | Create; import; invite | Create first item |
| Permission-denied | 403 or ACL check | "You don't have access" + request access | `role="alert"` | Request access; contact admin | Request access CTA |
| Disabled | Prereq not met or no permission | Muted button + tooltip "Why?" | `aria-disabled="true"` + `aria-describedby` | Hover/focus to see reason | Complete prereq |
| Partial | Some data loaded; some failed | Show available data + warning banner | `aria-live="polite"` warning | Use available data; retry failed parts | Retry failed parts |
| Timeout | Request exceeds threshold (e.g., 30s) | "Taking longer than expected" + uncertainty note | `aria-live="polite"` | Refresh to check; cancel | Refresh; retry |
| Optimistic | Action submitted; server pending | Immediate UI update (projected state) | `aria-busy="true"` on affected item | Undo (if available) | Rollback on error |
| Rollback | Optimistic update rejected by server | Revert UI + show error message | `role="alert"` for error | Retry; dismiss | Retry action |

### State Machine Decision Tree

```
For each async operation, apply:

STEP 1 — Define initial state:
  Does the user trigger this action? → starts in idle
  Does the page load trigger it?     → starts in loading immediately

STEP 2 — Define loading transition:
  Is it content layout? → skeleton loading
  Is it an action?      → spinner on button; disable submit
  Max duration before timeout: set AbortController timeout (e.g., 30s)

STEP 3 — Define success outcomes:
  Returns data:         → success state → render content
  Returns empty array:  → empty state → show CTA (not "no data")
  Returns 202 Accepted: → pending/processing state (not success yet; poll or websocket for completion)

STEP 4 — Define error outcomes:
  Network error:        → error state + retry button
  4xx client error:     → error state; no auto-retry (fix input first)
  5xx server error:     → error state + retry with backoff
  403 Forbidden:        → permission-denied state (not generic error)
  Timeout:              → timeout state + "may have completed" message

STEP 5 — Define disabled state:
  Why is the action unavailable? → document reason
  Is it temporary (loading)?    → show spinner, not disabled button
  Is it permanent (no permission)? → aria-disabled + describedby tooltip

STEP 6 — Define optimistic update rollback:
  Server confirms success? → keep optimistic state
  Server returns error?    → revert + show error + log for user action
```

# Selection Rules

Select this capability when **UI state completeness, feedback accuracy, and accessible state announcements** are the primary concern. Adjacent routing:

- Prefer `error-code-design` when the primary concern is backend error taxonomy and HTTP status semantics.
- Prefer `frontend-api-integration` when the primary concern is the data fetching lifecycle (caching, retry policy, request cancellation).
- Prefer `form-validation-design` when the primary concern is form field validation timing and submission state.
- Prefer `user-flow-modeling` when the primary concern is the ordered path through multi-step flows.
- Prefer `acceptance-standard-definition` when defining testable acceptance criteria from the state matrix.

# Risk Escalation Rules

Escalate when a state can cause: duplicate form submissions (double-charge, double-order); silent data loss (optimistic update not rolled back after server rejection); misleading success confirmation (202 Accepted displayed as "Done"); inaccessible error recovery (screen reader user cannot reach error message); leaked authorization state (permission-denied item reveals existence of resource to unauthorized user); or an unobservable long-running job (async job started; user has no progress visibility; no completion signal).

# Critical Details

- **The "202 Accepted is not success" trap.** An API returns `202 Accepted` — the job has been queued, not completed. The frontend shows a success toast: "Done!" User navigates away. The job fails asynchronously. User never knows. Fix: `202 Accepted` maps to a "processing/pending" state, not a success state. Show a "processing" indicator; poll for completion or use a WebSocket/SSE for job completion signal; show success only when the final status confirms completion.
- **AbortController for timeout.** Do not show a timeout state and then continue processing the response when it arrives 30 seconds later. Use `AbortController` to cancel the fetch request when the timeout threshold is exceeded. Without cancellation, the delayed response may update the UI in an unexpected way after the user has taken recovery action.
- **Skeleton layout matching.** A skeleton that does not match the real content layout causes a jarring layout shift when content loads. Skeleton placeholder dimensions should match the expected rendered content as closely as possible (WCAG 2.5.5; Core Web Vitals CLS metric).
- **`aria-disabled` vs `disabled`.** The HTML `disabled` attribute removes the element from tab order and makes it unreachable by keyboard. `aria-disabled="true"` preserves focus while communicating disabled state to assistive technology. Use `aria-disabled` for actions that are disabled but require explanation; prevent the action in JavaScript; link to explanation via `aria-describedby`.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Single loading spinner for loading, timeout, and error | User cannot distinguish "still loading" from "failed"; no recovery path shown |
| Empty container with no text or CTA | User sees blank screen; not sure if content exists or failed to load |
| Success toast on 202 Accepted | Async job may fail; user believes action completed; discovers failure hours later |
| Optimistic delete with no rollback on error | Item visually removed; server returns 500; item still exists; user confused; may duplicate delete attempt |
| `disabled` attribute with no explanation | Keyboard users skip button entirely; no context for why action unavailable |
| Error message outside DOM (e.g., console.log only) | Screen reader never announces error; blind users cannot recover |
| "Request cancelled" on timeout | Server may have processed; message is incorrect; user may avoid re-submitting valid action |

# Failure Modes

- Loading state persists forever on network error (no error state transition); user waits indefinitely; leaves the page.
- Empty list on first login treated as load error; generic "Something went wrong" shown; user files support ticket.
- Optimistic reorder of items; server returns 403; items remain in wrong order visually; database has original order; UI and DB diverge.
- 202 Accepted bulk import displayed as "Import complete"; background job fails; 0 records imported; user discovers 24 hours later.
- Disabled "Submit" button during loading uses HTML `disabled`; screen reader user tab-navigates past it with no information about why submission is not available.
- Timeout at 30s shows "Request cancelled"; server had committed the record; user re-submits; duplicate record created.
- Error toast injected into DOM without `role="alert"` or `aria-live`; screen reader does not announce; blind user has no error feedback.

# Output Contract

Return an interaction state matrix with:

- `states` (for each state: name, trigger, source signal from API/event, user-visible treatment, ARIA/accessibility treatment, allowed actions, blocked actions, preserved input/data, recovery path, backend dependency)
- `transitions` (valid state transitions; invalid/impossible transitions explicitly excluded)
- `disabled_states` (which actions can be disabled; why; how reason is communicated to user)
- `optimistic_updates` (which actions use optimistic update; rollback trigger; rollback treatment; user notification)
- `timeout_config` (timeout threshold per operation type; AbortController usage; timeout state message; uncertainty language)
- `empty_state_design` (per list/table/card: empty state content; CTA; distinguishes empty vs error vs permission-denied)
- `aria_regions` (live regions; alert roles; aria-busy; aria-disabled with describedby)
- `loading_treatment` (skeleton vs spinner decision per component; skeleton dimensions match content)
- `backend_alignment` (HTTP status → state mapping; 202 Accepted treatment; error code → error state mapping)
- `tests` (each state reached; ARIA announcement verified; optimistic rollback tested; timeout cancellation tested; disabled action accessible)

# Quality Gate

The state matrix is complete only when:

1. All applicable states defined: idle, loading, success, error, empty, disabled, partial, timeout, permission-denied, optimistic/rollback.
2. Empty distinguished from error and permission-denied (separate treatments).
3. Disabled actions use `aria-disabled` + `aria-describedby` (not HTML `disabled` without explanation).
4. Optimistic updates have explicit rollback treatment with user-visible error notification.
5. Timeout state uses uncertainty language; no "cancelled" until server confirms cancellation.
6. All status messages and error insertions use ARIA live regions or `role="alert"`.
7. 202 Accepted mapped to "processing/pending" state, not success state.
8. Backend error codes mapped to specific frontend states (not all errors → generic "error").
9. Tests cover every state in the matrix and verify ARIA announcements.
10. Skeleton placeholder dimensions documented to match content layout (CLS prevention).

# Used By

- experience-impact-modeler
- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `frontend-api-integration` for data fetching lifecycle and retry policy; `form-validation-design` for form field validation state and submission state machine; `acceptance-standard-definition` for testable criteria from state matrix; `backend-change-builder` if backend error semantics are undefined.

# Completion Criteria

The capability is complete when **every user-facing interaction has an explicit, accessible state model covering all failure and incomplete conditions** — with no impossible state combinations, no silent failures, and no state that leaves the user without an explanation and a recovery path.
