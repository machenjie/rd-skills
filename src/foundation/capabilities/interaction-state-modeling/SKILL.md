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

# Stage Fit

Use during experience-definition, implementation-planning, coding, bug-fix, debugging, code-review, refactoring, and testing when a user-facing surface has asynchronous, restricted, partial, or failure-prone behavior that must be explicit before implementation or approval. In planning, the matrix defines required states and source signals. In coding/review/refactoring, it becomes the contract for state transitions, accessibility announcements, retry/cancel behavior, backend alignment, validation, and tests. Hand off when the primary question is full journey order (`user-flow-modeling`), prototype hierarchy (`prototype-description`), backend error taxonomy (`error-code-design`), or design-system component governance (`design-system-rules`).

# Non-Negotiable Rules

- **Every async operation must have at minimum 4 states: idle, loading, success, error.** A two-state model (loading / done) is insufficient; it conflates success and error, and it has no idle baseline.
- **Empty state is not error state.** "No items found" (empty — data exists but query returns zero results) is different from "Failed to load" (error — network or server failure) and different from "You don't have access" (permission-denied — authorization failure). These must produce different UI treatments and different user actions.
- **Disabled actions must be reachable and explainable.** A button that is disabled because the user lacks permission or because a prerequisite is not met must: remain keyboard-focusable (not `disabled` attribute which removes focus); have an accessible tooltip or adjacent description explaining why it is disabled (WCAG 1.3.1 — Info and Relationships). A disabled button with no explanation violates heuristic 1 (visibility of system status).
- **Optimistic update rollback is mandatory when the server can reject the action.** If a UI applies an optimistic update (e.g., like button, reorder, delete) and the server returns an error, the UI must revert to the previous state and display an error message. Silent rollback (revert with no message) leaves the user confused. Visible rollback + error is required.
- **Timeout state must not imply cancellation unless confirmed.** "Request timed out" does not mean the server did not process the request — it may have committed but the response was lost. The timeout state message must reflect uncertainty: "This is taking longer than expected. The action may have completed — you can refresh to check." Never say "Action cancelled" when the server outcome is unknown.
- **State changes must be announced to assistive technology.** Loading indicators must use `aria-live="polite"` or `aria-live="assertive"` (for critical status) with descriptive text. Success and error messages injected into the DOM must use ARIA live regions or `role="alert"` so screen readers announce them (WCAG 4.1.3 — Status Messages, Level AA).
- **Frontend state must align with backend status semantics.** A frontend "success" state that shows before the server confirms durable commit is misleading. Match frontend state transitions to the actual HTTP response status and response body contract.
- **State ownership must be explicit.** The matrix must name whether each state is driven by local UI state, API status, background job status, permission policy, cached/stale data, or external dependency health. Unknown ownership is an implementation blocker or a handoff, not a reason to invent a UI state.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Basic async operation | Fetch, submit, save, search, refresh, or pagination has visible feedback. | Idle/loading/success/error plus allowed actions and ARIA status. | Operation source signal, loading treatment, error recovery, test obligation. | `frontend-api-integration`, `frontend-testing` | Full journey model. |
| Empty and filtered-empty model | List/table/card/search can return no records or no matches. | Empty vs filtered-empty vs not-found vs no-access vs load failure. | Query/filter context, permitted CTA, reset action, non-leaking copy. | `information-architecture`, `prototype-description` | Generic blank state. |
| Permission and disabled state | Action or content availability depends on role, ownership, feature flag, or prerequisite. | Reachable explanation, non-leaking permission copy, blocked/allowed actions. | Permission signal, prerequisite, accessible disabled treatment, denied-path test. | `permission-boundary-modeling`, `security-privacy-gate` when sensitive | Role names in user copy. |
| Optimistic or partial state | UI updates before durable confirmation, or some data/actions complete while others fail. | Rollback, preservation, partial warning, retry scope, no misleading success. | Previous state, rollback trigger, durable confirmation signal, recovery action. | `user-flow-modeling`, `idempotency-retry-design` | Silent rollback. |
| Long-running or timeout state | 202 Accepted, background job, polling, upload/import/export, or slow dependency. | Pending/processing vs complete, uncertain timeout language, cancel/refresh semantics. | Job status source, timeout threshold, cancellation truth, completion signal. | `async-job-design`, `frontend-api-integration` | Treating queued as done. |
| Accessibility-critical state | Modal, validation, destructive action, live results, or screen-reader-only status. | Live region, focus, keyboard, error announcement, color-independent feedback. | ARIA region, focus target, keyboard path, accessibility test. | `design-system-rules`, `frontend-testing` | Accessibility "later" pass. |

# Proactive Professional Triggers

- **Signal:** A UI request says "show loading/error" without source signals or transitions. **Hidden risk:** implementers invent incompatible state machines. **Required professional action:** produce the state matrix before coding. **Route to:** `interaction-state-modeling`, `frontend-api-integration`. **Evidence required:** source signal, transition, allowed actions, recovery, test.
- **Signal:** A list/table/search uses "no data" for all empty, filtered, permission, and failure outcomes. **Hidden risk:** users cannot tell whether to create, clear filters, request access, or retry. **Required professional action:** split empty-state meanings. **Route to:** `information-architecture`, `prototype-description`. **Evidence required:** condition, user copy intent, available CTA, non-leak rule.
- **Signal:** A disabled control is unreachable, unexplained, or implemented only with HTML `disabled`. **Hidden risk:** keyboard users cannot discover why the action is unavailable. **Required professional action:** require reachable explanation and blocked-action behavior. **Route to:** `design-system-rules`, `frontend-testing`. **Evidence required:** `aria-disabled`/description decision and keyboard assertion.
- **Signal:** A success toast appears before durable confirmation, on `202 Accepted`, or after an optimistic update. **Hidden risk:** false completion, data loss, duplicate action, or support escalation. **Required professional action:** separate accepted, processing, durable success, rollback, and timeout states. **Route to:** `async-job-design`, `idempotency-retry-design`. **Evidence required:** backend status mapping and durable completion signal.
- **Signal:** Retry/cancel/refresh appears after timeout or partial failure without idempotency or cancellation truth. **Hidden risk:** duplicate submit or incorrect "cancelled" message. **Required professional action:** define safe recovery semantics. **Route to:** `user-flow-modeling`, `backend-change-builder` when server semantics are missing. **Evidence required:** retry scope, idempotency/cancellation statement, preserved input/data.
- **Signal:** State behavior is based on old memory, previous bug reports, or generated context without current source confirmation. **Hidden risk:** stale state assumptions survive review. **Required professional action:** reconcile memory/graph/trajectory evidence with current source and validation. **Route to:** `repository-context-map`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected source, freshness limit, validation command or not-verified residual risk.

# Industry Benchmarks

Anchor against Nielsen visibility/error-recovery heuristics, WCAG 2.1/2.2 status-message and keyboard criteria, XState explicit-state modeling, TanStack Query/SWR/Remix request states, skeleton-vs-spinner guidance, form validation timing, and ARIA live-region practices. Keep root guidance limited to state ownership, evidence, routing, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for the detailed state matrix, decision tree, benchmark anchors, and anti-pattern review.

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

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 state-modeling rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a real state matrix, when timeout/permission/partial/optimistic evidence is uncertain, or when implementation is about to start. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed state matrices, benchmark anchors, decision trees, or anti-pattern review are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected matrix shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

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

- **Infinite loading:** network error has no error transition, so the user waits indefinitely and leaves the page.
- **Empty/error collapse:** first-login empty list is treated as load error, so the user sees generic failure instead of a starter path.
- **Optimistic divergence:** server rejects a reorder or delete, but the UI keeps the optimistic state and diverges from durable data.
- **Queued-as-done:** `202 Accepted` import is displayed as complete, then the background job fails without user-visible recovery.
- **Unreachable disabled action:** HTML `disabled` removes the action from keyboard focus and hides the reason from screen-reader users.
- **Unsafe timeout copy:** timeout says "cancelled" even though the server may have committed, leading to duplicate re-submit.
- **Unannounced error:** toast is injected without `role="alert"` or `aria-live`, so assistive technology never announces it.
- **Partial failure hidden:** one panel fails while other data loads, but the UI shows generic success and loses retry scope.

# Output Contract

Return an interaction state matrix with:

- `mode_selected` (basic async / empty-filtered-empty / permission-disabled / optimistic-partial / long-running-timeout / accessibility-critical)
- `operation_scope` (surface, user goal, source operation, entry trigger, affected components or actions)
- `states` (for each state: name, trigger, source signal from API/event, user-visible treatment, ARIA/accessibility treatment, allowed actions, blocked actions, preserved input/data, recovery path, backend dependency)
- `transitions` (valid state transitions; invalid/impossible transitions explicitly excluded)
- `state_ownership` (local UI, API response, cache, background job, permission policy, dependency health, or product decision owner for each state)
- `disabled_states` (which actions can be disabled; why; how reason is communicated to user)
- `optimistic_updates` (which actions use optimistic update; rollback trigger; rollback treatment; user notification)
- `timeout_config` (timeout threshold per operation type; AbortController usage; timeout state message; uncertainty language)
- `empty_state_design` (per list/table/card: empty state content; CTA; distinguishes empty vs error vs permission-denied)
- `aria_regions` (live regions; alert roles; aria-busy; aria-disabled with describedby)
- `loading_treatment` (skeleton vs spinner decision per component; skeleton dimensions match content)
- `backend_alignment` (HTTP status → state mapping; 202 Accepted treatment; error code → error state mapping)
- `tests` (each state reached; ARIA announcement verified; optimistic rollback tested; timeout cancellation tested; disabled action accessible)
- `handoff_boundaries` (what belongs to user flow, prototype brief, backend error contract, API integration, design-system review, or test gate)

# Evidence Contract

Close an interaction-state-modeling change only when the output names selected mode, boundaries inspected, source operation, backend or event signals inspected, state ownership, valid and invalid transitions, state/accessibility tests or review evidence, validation command with exit code or artifact/report path when available, freshness of source/graph/memory/trajectory evidence when used, what evidence proves and does not prove, residual risk, unresolved backend/product/design decisions, and next handoff owner. A generic "handle loading and errors" statement is not sufficient evidence.

# Benchmark Coverage

Behavior improvement should be validated structurally: baseline weak matrices usually collapse empty/error/permission, treat queued work as success, omit ARIA status, or leave retry/cancel behavior unsafe; treatment matrices must name mode, source signal, distinct states, ownership, transitions, accessible announcements, backend alignment, tests, and handoff boundaries. Token/turn overhead is acceptable only while this capability remains narrower than full flow modeling or frontend implementation design.

# Routing Coverage

Route here when state completeness and user feedback accuracy are primary. Guard against over-routing by handing off when the primary work is end-to-end journey order (`user-flow-modeling`), page hierarchy (`prototype-description`), backend error taxonomy (`error-code-design`), API caching/retry implementation (`frontend-api-integration`), design-system component semantics (`design-system-rules`), or test strategy (`frontend-testing` / `quality-test-gate`).

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
11. The selected mode, operation scope, and state ownership are explicit.
12. Valid and impossible transitions are named so implementation cannot enter contradictory states.
13. Retry, cancel, refresh, and navigation behavior preserve user input/data or state the loss warning.
14. Handoff boundaries and unresolved backend/product/design decisions are named with owner and blocking status.

# Used By

- experience-impact-modeler
- frontend-change-builder
- quality-test-gate

# Handoff

Hand off to `frontend-api-integration` for data fetching lifecycle and retry policy; `form-validation-design` for form field validation state and submission state machine; `acceptance-standard-definition` for testable criteria from state matrix; `backend-change-builder` if backend error semantics are undefined.

# Completion Criteria

The capability is complete when **every user-facing interaction has an explicit, accessible state model covering all failure and incomplete conditions** — with no impossible state combinations, no silent failures, and no state that leaves the user without an explanation and a recovery path.
