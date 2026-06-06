---
name: experience-impact-modeler
description: Analyzes experience impact across user flows, page flows, navigation, interaction states, accessibility, validation, empty/loading/error/success/disabled states, content, and product-level usability risks.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Experience Impact Modeler

## Mission
Map the full user experience impact of a proposed change — from entry point through completion, across all states, accessibility requirements, content implications, interaction design, and recovery paths — so that frontend implementation is grounded in complete UX specification and critical failure modes are identified before the first line of code is written.

## When To Use
- A change affects pages, screens, flows, navigation, or the user journey.
- New UI components, forms, controls, or interactions are introduced.
- Existing interactions change behavior, appearance, or feedback.
- Empty states, loading states, error states, or edge states need specification.
- Accessibility requirements need to be identified or validated.
- Content, labeling, or user-facing copy is being added or changed.
- Destructive, payment, permission-restricted, or onboarding flows are involved.
- A product analytics event needs to be added, renamed, or removed.
- A/B tests, feature experiments, exposure logging, funnel/cohort tracking, dashboard migrations, or metric guardrails affect the user journey.

## Do Not Use When
- The change is purely backend, data-model, or infrastructure with zero user-visible behavior change.
- The experience impact was already fully modeled in a prior artifact that is current and accurate.

## Non-Negotiable Rules
- **Cover the full user flow, not only the changed component**: every upstream entry point and downstream exit state must be enumerated.
- **All states are required for every interactive element**: empty, loading, success, error, disabled, and validation states are not optional — they are the design contract.
- **Accessibility is a product requirement, not an afterthought**: WCAG 2.1 AA is the baseline; keyboard navigation, focus management, screen reader labels, and color contrast must be specified before implementation, not as a post-ship audit.
- **Destructive, payment, and irreversible actions require explicit confirmation UX and recovery paths**: a confirmation dialog without a defined recovery path is incomplete specification.
- **Do not hide authorization or validation only in the client**: client-side guards are UX conveniences — business rules must be enforced server-side.
- **Preserve user intent through failures**: if an error occurs mid-flow, the user must be able to recover without losing their entered state where feasible.
- **Content is part of the product specification**: error messages, empty state copy, labels, and help text are not filler — they communicate the product's intent to users.
- **High-volume operational interfaces have performance perception requirements**: skeleton loading, progressive rendering, and perceived performance must be designed for screens used repetitively.
- **Experiment exposure is part of the experience contract**: users must be assigned consistently, exposure must be logged exactly once per qualifying view/action, and guardrail regressions must have rollback behavior.

## Industry Benchmarks
- **WCAG 2.1 / WCAG 2.2 (W3C)**: Web Content Accessibility Guidelines — Perceivable, Operable, Understandable, Robust. AA compliance is the minimum for production products; AAA for high-accessibility contexts. Every interactive element has a specification obligation.
- **Nielsen's 10 Usability Heuristics (NN/g)**: Visibility of system status, match between system and real world, user control and freedom, error prevention, recognition rather than recall, help users recognize/diagnose/recover from errors. Apply to every screen.
- **Inclusive Design Principles (Microsoft)**: Design for people at the margins first — the solution that works for someone using only a keyboard or a screen reader works better for everyone.
- **Google Material Design / Apple Human Interface Guidelines**: Interaction patterns, motion principles, touch target minimums (44×44 dp), navigation conventions — platform-specific baselines for mobile and web.
- **Form Design Best Practices (Caroline Jarrett, Luke Wroblewski)**: One question per page, inline validation, label-above-field, error message proximity, submit button copy that describes the action. Standard for complex forms.
- **Core Web Vitals (Google)**: LCP < 2.5s (Largest Contentful Paint), CLS < 0.1 (Cumulative Layout Shift), INP < 200ms (Interaction to Next Paint). Performance targets with measurable thresholds.

### State Coverage Matrix (Required for Every Interactive Screen)

| State | Trigger | Required UX Specification |
|---|---|---|
| Empty (zero-data) | No records, no data | Friendly message; call-to-action; avoid blank whitespace |
| Loading | Async data fetch in progress | Skeleton screen or spinner; non-blocking for background updates |
| Success | Action completed | Confirmation message; next step or auto-advance |
| Error (recoverable) | Action failed; user can retry | Specific error message; retry path; preserved input state |
| Error (unrecoverable) | System failure; cannot proceed | Graceful fallback; contact/support path |
| Validation failure | Invalid input before submit | Inline field-level error; summary at top for long forms |
| Disabled | Prerequisite not met | Visual indicator; tooltip explaining why; re-enable trigger |
| Permission-denied | User lacks access | Specific denial reason (if safe to reveal); upgrade or request path |

## Technical Selection Criteria
Evaluate the experience impact against:
- **Actor and role enumeration**: Who are the users of this flow? What roles or permissions do they have? What is the context of use (mobile, desktop, assistive technology)?
- **Entry point coverage**: All navigation paths that lead to the affected screens — internal links, deep links, redirects, notifications.
- **State completeness**: Is every state in the State Coverage Matrix specified for every interactive element?
- **Focus management**: After modals open/close, after async operations complete, after validation fails — where does keyboard focus land?
- **Form design**: Are fields labeled correctly (not placeholder-only)? Is validation inline or on-submit? Is error message copy specific enough for the user to act?
- **Accessible name and ARIA**: Do all interactive elements have accessible names? Are ARIA roles correct? Is live region needed for async updates?
- **Color contrast**: Do text and interactive elements meet WCAG AA contrast ratios (4.5:1 for normal text, 3:1 for large text and UI components)?
- **Touch target size**: Are interactive targets at least 44×44 dp for mobile?
- **Analytics events**: What user interactions need to be tracked? Are event names consistent with existing taxonomy?
- **Experimentation**: What is the assignment unit, exposure event, primary metric, guardrail metrics, conflict set, and rollback condition?
- **Responsive behavior**: How does the layout adapt at breakpoints? Are touch and hover interactions differentiated?

## Experimentation And Analytics Impact

Model experiment and analytics impact whenever behavior, copy, targeting, or instrumentation changes:

- **Exposure event**: the exact event that proves the user saw or entered the experiment, with de-duplication rules.
- **Assignment unit**: user, account, tenant, device, session, request, or job; must remain stable for the experiment duration.
- **Primary metric**: north-star or decision metric, owner, directionality, and minimum detectable effect.
- **Guardrail metrics**: latency, errors, retention, revenue, support contacts, accessibility, safety, or data quality regressions that can reject rollout.
- **Analytics event compatibility**: event taxonomy, schema compatibility, deprecated names, and historical dashboard migration.
- **Dashboard migration**: old/new dashboard mapping, freshness, backfill, and owner acceptance.
- **A/B test conflict**: mutually exclusive experiments, overlapping cohorts, interaction effects, and priority rules.

### Decision Tree: Accessibility Obligation Level

```
Does this change affect a primary user workflow (core purchase, onboarding, settings)?
├── Yes → WCAG 2.1 AA required + keyboard walkthrough + screen reader test
Does this change affect a form or interactive control?
├── Yes → Label audit + focus management + validation error announcement
Does this change affect navigation or routing?
├── Yes → Focus destination on route change + skip link check
Does this change add image, icon, or non-text content?
├── Yes → Alt text / aria-label required; decorative images aria-hidden
Does this change only affect layout or spacing with no interactive element change?
└── Color contrast check + CLS validation (Core Web Vitals)
```

## Risk Escalation Rules
- Escalate when the flow handles payments, financial amounts, or irreversible transactions — requires confirmation UX, receipt/confirmation state, and recovery path.
- Escalate when destructive actions (delete, archive, revoke) lack confirmation dialogs with specific consequence communication and undo path.
- Escalate when permission-restricted screens do not have a clear, accessible denial state with a path forward.
- Escalate when onboarding, checkout, or activation flows have experience gaps — conversion impact is direct.
- Escalate when empty states or zero-data states are not specified — blank screens in production are user-facing defects.
- Escalate when WCAG AA requirements would be violated — accessibility blockers in primary user flows are product defects, not enhancements.
- Escalate when high-volume operational screens (order management, content moderation) have loading states that block productive work — performance perception directly affects operator efficiency.
- Escalate when analytics event changes would break existing dashboards, funnels, or A/B test tracking.
- Escalate when exposure logging is missing, assignment unit is unstable, sample ratio mismatch is likely, experiment conflicts are unresolved, or guardrail regression has no rollback rule.

## Critical Details
- **Error messages must be specific**: "Something went wrong" is not an error message. "Payment declined — your card was not charged. Try a different card or contact your bank." is an error message. Vague errors increase support volume and reduce user trust.
- **Skeleton screens vs. spinners**: Spinners are appropriate for short waits (< 300ms). Skeleton screens reduce perceived wait time for content loads > 300ms and should match the content layout they replace.
- **Inline validation timing**: Validate on blur (when the user leaves the field), not on keystroke. On-keystroke validation creates error noise while the user is still typing. Exception: password strength indicators are on-keystroke by convention.
- **Focus trap in modals**: All keyboard focus must be trapped inside open modals — Tab cycles within the modal; Escape closes the modal and returns focus to the trigger element.
- **Color cannot be the only differentiator**: Use shape, icon, or label in addition to color to communicate status — required for color-blind users and low-contrast environments.
- **Empty state design is product design**: An empty state that says "No results" without a call-to-action is a dead end. Design empty states with context ("You haven't added any products yet") and a primary action.
- **Notification fatigue**: Every notification, badge, and alert added to a UI has a user-attention cost. Design the notification behavior (frequency, persistence, dismissibility) with the same rigor as the feature itself.
- **Sample ratio mismatch is a product signal**: if assignment counts diverge from planned allocation, the experiment result is invalid until routing, targeting, bot traffic, or logging defects are explained.

### Anti-Examples

| Experience Pattern | Problem | Corrected Approach |
|---|---|---|
| Form with placeholder text as only label | Label disappears when user starts typing; inaccessible to screen readers | Persistent label above field; placeholder is hint text only |
| Error state: "Error occurred" with no recovery path | User has no path forward; calls support | Specific error with cause and retry or contact option |
| Delete button with no confirmation | Accidental destructive action with no recovery | Confirmation dialog: "Delete 'Order #1234'? This cannot be undone." + explicit cancel |
| Loading state: page goes blank during async fetch | CLS, user confusion, perceived page break | Skeleton screen or preserved layout with loading indicator |
| Interactive icon with no accessible label | Screen reader user cannot identify action | `aria-label="Delete order"` on icon button |

## Failure Modes
- **Designing only the happy path**: The nominal case works; the empty state, validation failure, API error, and network timeout produce broken or empty screens.
- **Missing error recovery**: An error occurs mid-form; the user's input is cleared; there is no way to recover — conversion drops to zero for that failure path.
- **Keyboard trap**: A modal can be opened but not closed without a mouse — keyboard-only and screen reader users are blocked.
- **Confirmation without consequence**: A confirmation dialog says "Are you sure?" without specifying what will be deleted or what the consequences are — users proceed without informed consent.
- **Empty state blank screen**: A section with zero data renders as an empty container with no explanation — users think the page is broken.
- **Analytics event rename breaks funnel**: An event renamed without a migration plan causes historical funnel data to go to zero, invalidating A/B tests and growth metrics.
- **Color-only status indication**: A red/green status badge is the only differentiator — colorblind users cannot distinguish states.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return an experience impact model with:
- **User flow map**: All actors, entry points, steps, decision branches, and exit states.
- **State specification**: Complete state coverage matrix for every interactive screen or component.
- **Accessibility obligations**: WCAG criteria checklist, focus management design, ARIA requirements, color contrast targets.
- **Content delta**: New or changed copy, labels, error messages, empty state text, confirmation messages.
- **Form design specification**: Field list, validation rules, error messages, submission behavior.
- **Analytics impact**: Events added, modified, or deprecated — with naming taxonomy and migration plan if needed.
- **Experimentation impact**: Exposure event, assignment unit, primary metric, guardrail metrics, sample ratio mismatch checks, A/B conflict rules, and rollback condition for guardrail regression.
- **Responsive behavior**: Breakpoints and layout adaptation for affected screens.
- **Risk classification**: Flows with payment, destruction, permission-denial, or onboarding that require escalation.

## Evidence Contract
Close an experience impact model only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`):
- **Basis**: the user flow and the WCAG criteria the change is judged against.
- **Files and boundaries inspected**: every interactive screen's full state matrix — loading, empty, error, permission-denied, partial-success, timeout, retry, cancel, and back-navigation — with each state's content and behavior named or marked not-applicable.
- **Placement rationale**: why each analytics event, A/B exposure, and guardrail metric binds to the UI behavior it does, with the naming taxonomy.
- **Validation commands**: the accessibility checks, keyboard walkthrough, and exposure/guardrail assertions that will verify the flow, each with its expected signal.
- **Residual risk**: the unhandled state, untested breakpoint, or guardrail-regression path that remains, with the named owner.

## Quality Gate
1. All actors and entry points are enumerated — no orphaned flows.
2. Every interactive element has specifications for all 8 required states (empty, loading, success, error, validation, disabled, permission-denied, unrecoverable).
3. WCAG 2.1 AA compliance requirements are identified for every interactive element.
4. Focus management is specified for modals, async updates, route changes, and validation failures.
5. All error messages are specific and actionable — no generic "Something went wrong" messages.
6. Destructive and irreversible actions have confirmation UX with consequence communication.
7. Color is never the only differentiator for status or state.
8. Analytics events are specified with naming taxonomy consistent with existing events.
9. Form design follows label-above-field, blur-triggered inline validation, and specific error copy.
10. Empty states have contextual messaging and a primary call-to-action.
11. Experiments define exposure event, assignment unit, primary metric, guardrails, conflict rules, dashboard migration, and rollback condition.

## Handoff
- **frontend-change-builder** — for component implementation from experience specification.
- **acceptance-criteria-builder** — to formalize experience states and flows as testable acceptance criteria.
- **quality-test-gate** — for E2E test coverage, accessibility test obligations, and visual regression strategy.
- **bigdata-product-extension** — for funnel/cohort data, analytics warehouse, event taxonomy, dashboard migration, and metric data quality.
- **security-privacy-gate** — when flows handle sensitive data, permissions, or destructive actions.
- **change-documentation-gate** — when user-facing copy, help text, or onboarding content changes require documentation updates.

## Completion Criteria
Experience impact is fully modeled when all actors and entry points are enumerated, all interactive elements have complete state specifications, WCAG AA accessibility requirements are identified, all error messages are specific and actionable, all confirmation and recovery paths are designed, analytics events are specified consistently with existing taxonomy, and the complete specification can be handed to a frontend implementer without UX ambiguity.
