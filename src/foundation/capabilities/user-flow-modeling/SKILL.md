---
name: user-flow-modeling
description: Models user flows including entry points, success exits, failure exits, cancellation, retry, back navigation, and permission branches.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "08"
changeforge_version: 0.1.0
---

# Mission

**Model every path a user or automated actor takes through a workflow — including all entry points, decision branches, success exits, failure exits, cancellation paths, retry paths, back navigation, permission branches, and async completion states — so that dead ends, data loss on failure, unsafe retries, and permission ambiguity are eliminated by design, not discovered in user research or production incidents.**

# When To Use

Use this capability when: a change introduces or substantially modifies a multi-step task flow (checkout, onboarding, form wizard, document review, approval workflow, file import); a change affects navigation (route structure, deep link behavior, back button behavior, modal dismiss behavior); a change introduces asynchronous completion (file processing, payment capture, background job) where the user must receive feedback while waiting and on completion or failure; permission-based branching determines whether an actor can see, start, or complete a flow; or user input, partial progress, or uploaded data could be lost due to unhandled interruption, session timeout, or navigation away.

# Do Not Use When

Do not use this capability for: single-screen, stateless interactions with no branching and no navigation (a search box that returns results on the same page with no state transitions); defining visual design, layout, or component-level interaction (use `interaction-state-modeling`); modeling domain actor goals and behavioral contracts (use `use-case-modeling`); information architecture and content organization decisions (use `information-architecture`).

# Non-Negotiable Rules

- **Identify every entry point explicitly.** A flow without enumerated entry points cannot be tested for access control or deep link behavior. Entry points include: direct URL navigation, link from another flow, email deep link, push notification, OAuth redirect, API webhook redirect, programmatic navigation after an action. Each entry point must specify its authentication requirement, required URL parameters, and what state the user must be in to enter this flow from this entry point.
- **Identify every exit explicitly: success exits, failure exits, cancellation exits, and timeout exits.** A flow with only a success exit is a trap — users who encounter an error, who cancel, or whose session times out have no defined path. Each exit must specify: what UI state the user sees, what system state persists, whether progress is preserved or discarded, and where the user is navigated to next. A failure exit must not navigate the user to a blank page or an error state they cannot recover from without restarting the entire flow.
- **Preserve user input and partial progress across recoverable interruptions.** A "recoverable interruption" is any event that interrupts the flow but does not invalidate the user's intent: browser tab switch, phone call, session timeout, temporary network outage, page refresh. If the user re-enters the flow after an interruption, what they had entered must either be preserved (draft auto-save) or the user must be warned before their progress is lost (unsaved changes dialog). Silently discarding user input on navigation away is a UX defect that causes abandonment and support contacts.
- **Define what the user can safely do after partial completion.** If step 3 of a 5-step flow has completed and the user navigates away or is interrupted, they must have a defined re-entry path that brings them back to step 4 without repeating steps 1–3. If re-entering from step 1 would cause a duplicate side effect (duplicate payment, duplicate record creation), the flow must detect the partial state and route the user appropriately. "Partial completion" is not an edge case — it is the most common state for abandoned multi-step flows.
- **Tie every branch condition to a testable assertion.** A branch labeled "if authorized" is not testable — it is a vague label. A branch labeled "if `user.role === 'admin'` AND `feature_flag.bulk_export === true`" is testable: it specifies the exact condition, enabling a permission matrix test. Every branch condition in the flow must be expressible as a boolean predicate on system state.
- **Retry paths must specify idempotency behavior and intermediate state handling.** A retry that re-executes a payment charge without idempotency protection causes a double charge. A retry that re-submits a form that has already been partially processed may create duplicate records. The retry design must specify: is the retried action idempotent by design (same result if executed twice)? Is an idempotency key required? What is the maximum retry count? What state is the record in between the initial attempt and the retry?

# Industry Benchmarks

Anchor against: **Jesse James Garrett — The Elements of User Experience** — flow as the connection between information architecture and interaction design. **Journey Mapping (Nielsen Norman Group)** — multi-step user journeys with touchpoints, emotions, and decision points. **Task Analysis (Hierarchical Task Analysis)** — decomposing tasks into subtasks; goal/operation/plan structure. **Google Material Design — Navigation patterns** — back navigation semantics; up navigation vs. back navigation; deep link handling; state preservation on navigation. **WCAG 2.2 — SC 3.3.4 (Error Prevention)** — reversible submissions; confirmation gates for irreversible or consequential actions; re-enterable forms. **WCAG 2.2 — SC 2.4.3 (Focus Order)** — navigation must be logical and predictable; branching flows must maintain keyboard navigation integrity. **HTML History API / React Router / Next.js router** — `pushState`/`replaceState` for deep link support; `beforeunload` for unsaved changes; shallow routing for state changes without navigation. **RFC 7807 (Problem Details for HTTP APIs)** — structured error response format; error detail must support user-facing error message derivation. **OAuth 2.0 / PKCE — RFC 7636** — redirect flows with `state` parameter for CSRF protection and return URL preservation after authentication redirects.

### Flow Node Type Classification Matrix

| Node Type | Description | Required Design Elements | Failure to Handle Risk |
| --- | --- | --- | --- |
| Entry point | Where the user enters the flow | Auth requirement; required params; state precondition | Unauthorized access; broken deep links |
| Decision branch | Conditional fork based on system or user state | Boolean predicate (testable); both branch paths defined | Users routed to undefined state |
| Action step | User submits data or triggers system action | Idempotency; loading state; error feedback; retry behavior | Duplicate submissions; silent failures |
| Wait state | Async operation in progress (job, payment) | Progress feedback; polling or push update; timeout exit; failure exit | User abandons; status unknown |
| Partial completion checkpoint | User has completed some steps; may re-enter | Resume path; re-entry detection; duplicate prevention | Duplicate records; user forced to restart |
| Success exit | Flow completed successfully | Confirmation; next action suggestion; breadcrumb cleared | User has no confirmation; re-enters flow |
| Failure exit | Flow cannot complete; error state | Error message (non-revealing); recovery options; support path | Dead end; user abandonment |
| Cancellation exit | User abandons; flow discarded | Draft deletion or preservation; navigation target; side effect rollback | Orphaned records; data leakage |
| Permission branch | Actor lacks authorization for a path | Non-revealing error (no data disclosure); escalation path | Privilege disclosure; unauthorized access |

### Flow Interruption Decision Tree

```
User navigates away from an in-progress form / multi-step flow:
  Has the user entered any data that is not yet submitted?
    NO  → Allow navigation freely; no warning needed
    YES → Is the flow re-entrant? (can the user resume from where they left off?)
          YES → Auto-save draft; navigate; show "Resume your application" on return
          NO  → Show unsaved changes dialog:
                "You have unsaved changes. Leave anyway?" [Leave] [Stay]
                If [Leave]: discard draft; cancel any created records; navigate
                If [Stay]: return to flow; cursor restored to last input

Session expires while user is mid-flow:
  Is partial data server-side?
    YES → Preserve server-side draft for [N] hours; redirect to login with returnTo param
          After re-auth: redirect to returnTo; resume from last completed step
    NO  → Form data is lost; redirect to login; show re-entry message
          If this is unacceptable: add server-side draft persistence before session timeout

Async operation completes while user has navigated away:
  → Send push notification or in-app notification
  → Deep link back to flow result view
  → Do not send operation result to email as primary feedback for time-sensitive actions
```

# Selection Rules

Select this capability when **ordered path and branching behavior across multiple steps, screens, or states is the primary design question**. Route to `information-architecture` when content hierarchy and navigation structure are the primary concern. Route to `interaction-state-modeling` when single-screen component state behavior is the primary concern. Route to `use-case-modeling` when the behavioral contract (actor goal, preconditions, postconditions) is the primary concern. Route to `routing-navigation-design` when route-level access guards and URL structure are the primary concern.

# Risk Escalation Rules

Escalate when: a flow branch can lose user-entered data without warning (data loss risk — must add unsaved changes protection); a retry path can create duplicate financial records, duplicate orders, or duplicate account creations (idempotency risk — must design idempotency key before implementation); a permission branch can expose the existence of restricted resources through error message, count, or URL pattern (IDOR/information disclosure risk — must implement non-revealing error); a flow leaves users in a wait state with no timeout or failure exit (stuck state risk — must add timeout and failure exit); or a cancellation path does not roll back previously committed side effects (orphaned record risk — must design compensation or cleanup).

# Critical Details

- **Back navigation behavior is the most under-specified element in multi-step flows.** "Back button takes user to previous step" sounds obvious — but: does it preserve the data the user entered on the current step? does it revert any server-side changes made on the current step? does it maintain the state of steps the user has already completed? is the behavior different for browser back button vs. in-app back button? For flows with server-side state changes at each step, back navigation must either be a server-side "undo" operation or a "view only" mode that prevents modification of completed steps.
- **Async completion states require three distinct UI states, not one.** When a background operation is in progress, there are three possible states the user can be in: (1) in the flow, watching the progress indicator; (2) navigated away from the flow, unaware of progress; (3) returned to the flow after the operation completed (success or failure). Each of these three states must have a defined UI and a defined user action path. A flow that only handles state (1) will leave users in states (2) and (3) with no feedback.
- **Permission branches must not reveal the existence of restricted resources.** If a user navigates to a flow that requires a permission they do not have, the error must not reveal: that the resource exists (return 404, not 403 for sensitive resources); that other users have the resource; or what additional permissions would be required. This is the OWASP A01:2021 Broken Access Control requirement applied to UX. The UX message must be "This page is not available" rather than "You don't have admin access to view this order."
- **Idempotency keys for flow submissions must be generated client-side and submitted with the form.** A server-generated idempotency key cannot prevent double submission — if the user clicks "Submit" twice before the first response arrives, two requests reach the server without an idempotency key. The correct pattern: generate a UUID on form load (`formSessionId = uuid()`); include it in every submission of this form instance; the server treats a second submission with the same `formSessionId` as a duplicate and returns the original response.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Multi-step checkout: no "resume from partial completion" | User closes browser after step 2; returns next day; must start over; abandonment rate 40% | Server-side draft with session token; "resume your order" prompt on return |
| Retry button re-POSTs form without idempotency key | User retries after network error; duplicate order created; customer charged twice | Client-generated `formSessionId` UUID; server deduplicates on this key |
| Permission branch: 403 error reveals "You need admin role" | Attacker learns which resources require admin; targeted privilege escalation attempts | Generic "Page not available" message; no role name in response; log the attempt |
| Back button on step 3 does not revert server-side step-3 action | User "backs" to fix an error; step-3 action already committed; duplicate when user resubmits | Back button triggers server-side step-3 undo; or back is "view only" with warning |
| Async file upload: no failure exit | File processing fails after 10 min; user sees spinner forever; no way to retry or cancel | Timeout after 5 min; failure exit with "Upload failed — try again"; link to support |
| Cancellation exits flow without rolling back created records | User cancels mid-onboarding; PENDING account record exists; re-registration fails | Cancellation triggers cleanup job: delete PENDING account; purge uploaded files |

# Failure Modes

- User submits form; network error; clicks retry; duplicate record created; duplicate charge.
- User is mid-checkout; session expires; re-logs in; cart is empty; abandons purchase.
- Permission branch returns 403 with role name in error message; attacker maps permission model.
- Async export job runs for 20 minutes; user navigated away; job completes; no notification; user re-runs job; duplicate export.
- Back navigation on step 3 does not revert server action from step 3; user experiences unexpected state on resubmission.
- Cancellation at step 4 leaves a PENDING subscription record; user cannot re-subscribe.

# Output Contract

Return a flow model with:

- `entry_points` (per entry: URL/trigger, auth requirement, required params, state precondition)
- `flow_steps` (per step: node type, action/decision, success path, failure path)
- `branch_conditions` (per branch: boolean predicate, both branch destinations)
- `success_exits` (destination, system state, confirmation message)
- `failure_exits` (error message design, recovery options, support path)
- `cancellation_exits` (data preserved or discarded, server-side cleanup, navigation target)
- `retry_design` (idempotency key strategy, max retry count, intermediate state)
- `back_navigation_design` (per step: back behavior, state preserved, server-side revert if needed)
- `async_states` (in-flow progress; navigated-away notification; return-to-result design)
- `permission_branches` (per authorization gate: non-revealing error, escalation path)
- `partial_completion` (re-entry path, draft preservation, duplicate prevention)
- `interruption_handling` (unsaved changes dialog trigger, draft auto-save strategy)
- `verification_points` (testable assertions at each decision branch)

# Quality Gate

The flow model is complete only when:

1. All entry points have authentication and precondition specifications.
2. Every decision branch has a Boolean predicate and both destinations defined.
3. Success, failure, cancellation, and timeout exits are all defined.
4. User data is explicitly preserved or discarded at every interruption point.
5. Partial completion re-entry path prevents duplicate side effects.
6. Retry paths have idempotency key design.
7. Back navigation behavior is specified for every step with server-side state changes.
8. Async operations have in-flow, away, and return states.
9. Permission branches use non-revealing error messages.
10. Every flow step has a verification point expressible as a testable assertion.

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `interaction-state-modeling` for per-screen component state design; `acceptance-standard-definition` for testable criteria from flow verification points; `backend-change-builder` for retry idempotency and cancellation server guarantees; `routing-navigation-design` for route guard and deep link implementation.

# Completion Criteria

The capability is complete when **every path through the flow has a defined user outcome and system state, no dead ends exist, user data is explicitly preserved or discarded at every interruption, and every branch condition is testable**.
