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

# Stage Fit

Owns experience-definition, implementation-planning, coding, bug-fix, debugging, code-review, refactoring, testing, release-readiness, and final handoff when the primary concern is the ordered path through a user or actor workflow across steps, screens, redirects, async waits, permission branches, interruption, retry, and exits. In planning, it turns product intent, current routes, screens, state models, analytics or support signals, and test paths into a flow graph with explicit user and system outcomes. In coding and refactoring, it keeps route, state, permission, retry, and async implementation aligned with the accepted flow graph instead of letting individual screens invent branches. In debugging, separate flow-order defects, route-guard defects, state-model defects, backend idempotency gaps, and stale deep-link evidence before changing the journey. In review and testing, reject happy-path-only journeys, dead ends, unsafe retries, ambiguous back navigation, unverified permission branches, stale deep links, and flow evidence copied from project memory or repository graph without current-source confirmation. In release-readiness, require fresh validation after the final entry, branch, exit, retry, permission, async, interruption, or back-navigation edit. Hand off when the primary question is page hierarchy, component state, route guard implementation, backend idempotency, or acceptance test strategy.

# Non-Negotiable Rules

- **Identify every entry point explicitly.** A flow without enumerated entry points cannot be tested for access control or deep link behavior. Entry points include: direct URL navigation, link from another flow, email deep link, push notification, OAuth redirect, API webhook redirect, programmatic navigation after an action. Each entry point must specify its authentication requirement, required URL parameters, and what state the user must be in to enter this flow from this entry point.
- **Identify every exit explicitly: success exits, failure exits, cancellation exits, and timeout exits.** A flow with only a success exit is a trap — users who encounter an error, who cancel, or whose session times out have no defined path. Each exit must specify: what UI state the user sees, what system state persists, whether progress is preserved or discarded, and where the user is navigated to next. A failure exit must not navigate the user to a blank page or an error state they cannot recover from without restarting the entire flow.
- **Preserve user input and partial progress across recoverable interruptions.** A "recoverable interruption" is any event that interrupts the flow but does not invalidate the user's intent: browser tab switch, phone call, session timeout, temporary network outage, page refresh. If the user re-enters the flow after an interruption, what they had entered must either be preserved (draft auto-save) or the user must be warned before their progress is lost (unsaved changes dialog). Silently discarding user input on navigation away is a UX defect that causes abandonment and support contacts.
- **Define what the user can safely do after partial completion.** If step 3 of a 5-step flow has completed and the user navigates away or is interrupted, they must have a defined re-entry path that brings them back to step 4 without repeating steps 1–3. If re-entering from step 1 would cause a duplicate side effect (duplicate payment, duplicate record creation), the flow must detect the partial state and route the user appropriately. "Partial completion" is not an edge case — it is the most common state for abandoned multi-step flows.
- **Tie every branch condition to a testable assertion.** A branch labeled "if authorized" is not testable — it is a vague label. A branch labeled "if `user.role === 'admin'` AND `feature_flag.bulk_export === true`" is testable: it specifies the exact condition, enabling a permission matrix test. Every branch condition in the flow must be expressible as a boolean predicate on system state.
- **Retry paths must specify idempotency behavior and intermediate state handling.** A retry that re-executes a payment charge without idempotency protection causes a double charge. A retry that re-submits a form that has already been partially processed may create duplicate records. The retry design must specify: is the retried action idempotent by design (same result if executed twice)? Is an idempotency key required? What is the maximum retry count? What state is the record in between the initial attempt and the retry?
- **Closure evidence must name the flow validator or test command, validator/tool, artifact or report path, output and exit code or manual review result, changed entry/step/branch/exit/retry/permission/async scope, and freshness after the final flow-related edit.** Repository graph, project memory, analytics snippets, or old E2E results are search leads, not proof of the current flow.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New or changed journey | New multi-step task, wizard, checkout, onboarding, approval, import, export, or review path. | Complete entry-to-exit flow graph with user and system state at each node. | Actor/goal, current entry points, steps, exits, branch predicates, and changed-path-to-test map. | `information-architecture`, `prototype-description` | Visual layout or component API detail. |
| Recovery and interruption flow | Refresh, tab close, session expiry, network loss, partial completion, abandoned draft, or resume path matters. | Preserve or intentionally discard progress with re-entry and duplicate prevention. | Draft/partial state owner, re-entry rule, warning/copy, cleanup or compensation path. | `interaction-state-modeling`, `backend-change-builder` | Silent data loss or restart-only recovery. |
| Retry, idempotency, and side-effect flow | Submit, pay, create, import, export, or job retry can repeat a side effect. | Safe retry/cancel/refresh behavior and intermediate states. | Idempotency key, operation status, max retry, duplicate detection, and residual unknowns. | `idempotency-retry-design`, `data-side-effect-flow-tracing` | Re-POST button without idempotency evidence. |
| Permission and deep-link branch | Role, ownership, tenant, feature flag, notification, email link, or direct URL changes reachability. | Non-leaking branch behavior and safe route recovery. | Guard condition, sensitive-resource disclosure policy, deep-link source, and denied-path test. | `permission-boundary-modeling`, `routing-navigation-design`, `security-privacy-gate` when sensitive | Revealing role/resource existence in user copy. |
| Async wait and completion flow | Background job, payment capture, upload, processing, polling, push notification, or return-to-result path. | In-flow, away, timeout, failure, and return states. | Job status source, timeout threshold, completion signal, notification/deep-link behavior, and failure exit. | `async-job-design`, `interaction-state-modeling` | Spinner-only wait states. |

# Industry Benchmarks

Anchor against Garrett's UX structure layer, NN/g journey mapping and task analysis, Material navigation semantics, WCAG error-prevention and focus-order criteria, History API router behavior, Problem Details for recoverable errors, and OAuth/PKCE redirect-state preservation. Keep this body focused on mode selection and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for node classification, interruption decision trees, and detailed anti-pattern review.

# Selection Rules

Select this capability when **ordered path and branching behavior across multiple steps, screens, or states is the primary design question**. Route to `information-architecture` when content hierarchy and navigation structure are the primary concern. Route to `interaction-state-modeling` when single-screen component state behavior is the primary concern. Route to `use-case-modeling` when the behavioral contract (actor goal, preconditions, postconditions) is the primary concern. Route to `routing-navigation-design` when route-level access guards and URL structure are the primary concern.

# Risk Escalation Rules

Escalate when: a flow branch can lose user-entered data without warning (data loss risk — must add unsaved changes protection); a retry path can create duplicate financial records, duplicate orders, or duplicate account creations (idempotency risk — must design idempotency key before implementation); a permission branch can expose the existence of restricted resources through error message, count, or URL pattern (IDOR/information disclosure risk — must implement non-revealing error); a flow leaves users in a wait state with no timeout or failure exit (stuck state risk — must add timeout and failure exit); or a cancellation path does not roll back previously committed side effects (orphaned record risk — must design compensation or cleanup).

# Proactive Professional Triggers

- **Signal:** A requested journey describes only the happy path or final success screen. **Hidden risk:** failure, cancellation, permission, timeout, and back-navigation branches become implementation guesses. **Required professional action:** model all exits and branch predicates before implementation. **Route to:** `user-flow-modeling`, `acceptance-standard-definition`. **Evidence required:** flow graph, branch table, exit state, and verification point per branch.
- **Signal:** Repository graph, route list, analytics, support reports, project memory, or prior execution trajectory suggests a known flow to reuse. **Hidden risk:** stale or partial flow evidence can preserve old dead ends. **Required professional action:** confirm the candidate against current routes, screens, state contracts, tests, and product constraints. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected current paths, accepted/rejected reused pattern, freshness limit, and evidence limits.
- **Signal:** A step submits, creates, pays, imports, exports, sends, or starts a job and then offers retry, refresh, or back navigation. **Hidden risk:** duplicate side effects, orphaned records, or misleading completion. **Required professional action:** define idempotency, intermediate state, safe retry, and compensation or cleanup. **Route to:** `idempotency-retry-design`, `data-side-effect-flow-tracing`, `backend-change-builder`. **Evidence required:** idempotency key/source, operation status, rollback/compensation owner, and not-verified residual risk.
- **Signal:** Direct URLs, notifications, email links, OAuth redirects, or permission-specific entry points can enter mid-flow. **Hidden risk:** broken deep links, unauthorized state disclosure, or lost return intent. **Required professional action:** map entry preconditions and non-leaking denied/unavailable/not-found outcomes. **Route to:** `routing-navigation-design`, `permission-boundary-modeling`, `security-privacy-gate` when sensitive. **Evidence required:** entry table, guard condition, return path, disclosure policy, and denied-path test.
- **Signal:** Async completion can occur while the user is in-flow, away, timed out, or returning later. **Hidden risk:** user cannot tell whether work completed, failed, or is safe to retry. **Required professional action:** model in-flow progress, away notification, timeout wording, failure exit, and return-to-result path. **Route to:** `interaction-state-modeling`, `async-job-design`. **Evidence required:** status source, timeout threshold, notification/deep-link behavior, and completion verification.
- **Signal:** Prior validation, repository graph, analytics, support notes, project memory, or execution trajectory says a journey is proven before route, screen, guard, retry, async, or cancellation behavior changes. **Hidden risk:** stale evidence preserves a dead end, unsafe retry, or permission leak in the new flow. **Required professional action:** rerun, replace, or downgrade the proof and record validation freshness. **Route to:** `validation-broker`, `plan-execution-consistency`. **Evidence required:** changed path, validator/report path, exit code or manual artifact, what the stale evidence no longer proves, and residual risk owner.

# Critical Details

- **Back navigation behavior is the most under-specified element in multi-step flows.** "Back button takes user to previous step" sounds obvious — but: does it preserve the data the user entered on the current step? does it revert any server-side changes made on the current step? does it maintain the state of steps the user has already completed? is the behavior different for browser back button vs. in-app back button? For flows with server-side state changes at each step, back navigation must either be a server-side "undo" operation or a "view only" mode that prevents modification of completed steps.
- **Async completion states require three distinct UI states, not one.** When a background operation is in progress, there are three possible states the user can be in: (1) in the flow, watching the progress indicator; (2) navigated away from the flow, unaware of progress; (3) returned to the flow after the operation completed (success or failure). Each of these three states must have a defined UI and a defined user action path. A flow that only handles state (1) will leave users in states (2) and (3) with no feedback.
- **Permission branches must not reveal the existence of restricted resources.** If a user navigates to a flow that requires a permission they do not have, the error must not reveal: that the resource exists (return 404, not 403 for sensitive resources); that other users have the resource; or what additional permissions would be required. This is the OWASP A01:2021 Broken Access Control requirement applied to UX. The UX message must be "This page is not available" rather than "You don't have admin access to view this order."
- **Idempotency keys for flow submissions must be generated client-side and submitted with the form.** A server-generated idempotency key cannot prevent double submission — if the user clicks "Submit" twice before the first response arrives, two requests reach the server without an idempotency key. The correct pattern: generate a UUID on form load (`formSessionId = uuid()`); include it in every submission of this form instance; the server treats a second submission with the same `formSessionId` as a duplicate and returns the original response.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 flow-modeling selection and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete flow, when entry/exit/retry/back/permission coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when node classification, interruption decision trees, or detailed anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

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

- **Unsafe retry:** User submits form, sees a network error, clicks retry, and creates a duplicate record or duplicate charge because the flow lacked idempotency and intermediate state handling.
- **Interrupted checkout loss:** User is mid-checkout, session expires, re-authenticates, finds the cart or draft empty, and abandons because interruption and re-entry were not designed.
- **Permission disclosure:** Permission branch returns `403` with a role name or resource-specific message, allowing an attacker to map restricted resources and privilege boundaries.
- **Async away-state gap:** Export job runs for 20 minutes, user navigates away, job completes without notification or result route, and the user starts a duplicate export.
- **Back-navigation replay:** Browser back or in-app back reaches a side-effecting step after submission, causing stale state, duplicate action, or inconsistent confirmation.
- **Cancellation orphan:** Cancellation at step 4 leaves a `PENDING` subscription, uploaded file, or job record that blocks the user from restarting safely.
- **Stale journey proof:** Project memory or old E2E output says the flow is covered, but new route guards, deep links, or async states were added after that validation.
- **Validation map gap:** Changed entry, branch, cancellation, retry, or permission path has no validator, manual review artifact, or named residual owner, so handoff over-claims flow safety.

# Output Contract

Return a flow model with:

- `mode_selected` (new/changed journey, recovery/interruption, retry/idempotency, permission/deep-link, or async wait/completion)
- `flow_scope` (actor, goal, owning product surface, current route/screen boundary, and excluded surfaces)
- `source_evidence` (current routes, screens, state models, analytics/support signals, repository graph, project memory, execution trajectory, tests, and freshness limits)
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
- `changed_flow_to_validation_map` (each changed entry, step, branch, exit, retry, permission, or async state mapped to test/validator or residual risk)
- `validation_commands` (flow, route, accessibility, E2E, or manual-review command; validator/tool; artifact/report path; relevant output; exit code or manual result; changed flow scope; and freshness verdict)
- `handoff_boundaries` (what belongs to IA, prototype, state modeling, route design, backend idempotency, security, or test gates)
- `evidence_limits` (what was not verified: live analytics, production routes, real browser behavior, backend idempotency, permission enforcement, or E2E coverage)

# Evidence Contract

Close a user-flow-modeling change only when the output names selected mode, flow scope, current source evidence inspected, boundaries inspected, repository graph/project memory/execution trajectory freshness when used, actor goal, all entries, all exits, branch predicates, retry/idempotency behavior, back/cancel/interrupt behavior, async completion states, permission disclosure policy, changed-flow-to-validation map, validation evidence, evidence limits, residual risk, and next handoff owner. A linear happy path or "user can complete the flow" statement is not sufficient evidence.

State what evidence proves, what evidence does not prove, reuse and placement rationale for any route graph, journey pattern, analytics/support signal, project memory, or execution trajectory claim, behavior preservation for existing entry points/deep links/tests, and the next gate before handoff. Validation evidence must include command names, validator/tool, artifact/report path, relevant output, exit code or manual review result, changed flow scope, and freshness after the final material edit; stale journey maps, graph-only evidence, or happy-path-only E2E proof must be downgraded to residual risk.

# Benchmark Coverage

Behavior improvement should be validated structurally: weak flow models usually show only the success path, hide retry side effects, omit failure/cancel/timeout exits, conflate permission and not-found states, ignore browser back, or reuse stale journey memory. Improved outputs must name mode, flow scope, source evidence, entry/exit coverage, branch predicates, recovery semantics, validation mapping, and handoff boundaries while keeping detailed benchmark examples in references.

# Routing Coverage

Route here when ordered journey behavior across multiple steps, screens, redirects, async states, permissions, recovery paths, or partial completion is primary. Guard against over-routing by handing off when the primary concern is navigation labels and grouping (`information-architecture`), one-surface UI brief (`prototype-description`), component states (`interaction-state-modeling`), route guard/URL mechanics (`routing-navigation-design`), backend retry/idempotency (`idempotency-retry-design` / `backend-change-builder`), or acceptance/test strategy (`acceptance-standard-definition` / `quality-test-gate`).

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
11. Selected mode, flow scope, current source evidence, and excluded surfaces are explicit.
12. Repository graph, project memory, and execution trajectory evidence are source-confirmed or marked not verified.
13. Each changed entry, branch, exit, retry, permission, async, interruption, or back-navigation path maps to a validator, test, or named residual risk.
14. Validation commands, validators, artifacts/reports, output and exit code or manual result, changed flow scope, and freshness are recorded for every accepted entry, step, branch, exit, retry, permission, async, interruption, and back-navigation claim.
15. Handoff boundaries and evidence limits are named so flow evidence is not over-claimed as IA, component state, route guard, backend idempotency, security, or E2E proof.

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `information-architecture` for navigation grouping and labels; `prototype-description` for single-surface implementation briefs; `interaction-state-modeling` for per-screen loading, empty, error, disabled, timeout, optimistic, and accessibility states; `routing-navigation-design` for route guards, deep links, redirects, stale links, and history mechanics; `idempotency-retry-design` or `backend-change-builder` for retry, cancellation, compensation, and server guarantees; `permission-boundary-modeling` or `security-privacy-gate` for sensitive permission disclosure risk; and `acceptance-standard-definition` / `quality-test-gate` for verification points and E2E coverage.

# Completion Criteria

The capability is complete when **every path through the flow has a defined user outcome and system state, no dead ends exist, user data is explicitly preserved or discarded at every interruption, and every branch condition is testable**.
