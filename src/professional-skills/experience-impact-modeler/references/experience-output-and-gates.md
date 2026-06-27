# Experience Output And Gates

Load this reference when `experience-impact-modeler` needs deeper experience proof than the body checklist can carry. Keep the skill body compact; use this file for state-to-validation mapping, graph/memory/trajectory coupling, analytics proof, and closure gates.

## Flow Evidence Matrix

| Dimension | Required Question | Evidence Pattern | Stop Condition |
|---|---|---|---|
| Actors and roles | Which user, account, tenant, permission, device, or assistive technology context enters the flow? | Actor table with role, entry point, permission state, and device context. | A role can reach the screen but has no modeled success, denial, or recovery path. |
| Entry and exit graph | Which routes, deep links, redirects, notifications, and back-navigation paths enter or leave the flow? | Route graph with entry, decision, completion, cancel, retry, and return paths. | The changed screen is modeled without upstream or downstream navigation. |
| State coverage | What does the user see for empty, loading, success, error, validation, disabled, permission-denied, timeout, partial success, cancel, and retry? | State table per screen or component with copy, focus, persistence, and recovery. | Any interactive element has an unowned state or vague "handle error" note. |
| Content and intent | Does copy explain what happened, what will happen, and how to recover? | Content delta table for labels, helper text, empty states, confirmations, and errors. | Copy is generic, ambiguous, or disconnected from the user's next action. |
| Responsive behavior | How does the flow change across mobile, tablet, desktop, hover, touch, and reduced-motion settings? | Breakpoint notes, overflow checks, target-size checks, and motion fallback. | The primary action, error, or recovery path becomes hidden or unreachable. |

## Accessibility And Recovery Gates

- **Keyboard path**: tab order, focus trap, Escape behavior, route-change focus destination, and focus restoration must be named for every modal, drawer, toast, validation error, and async update.
- **Screen reader behavior**: accessible name, role, description, live region, announcement timing, and hidden/decorative content decisions must be explicit.
- **Visual perception**: contrast, non-color status indicator, target size, text resizing, reduced motion, and layout shift obligations must be stated.
- **Input preservation**: failed submit, timeout, refresh, back-navigation, and permission transition must preserve recoverable user input or explain why preservation is unsafe.
- **Recovery path**: every recoverable error needs retry, cancel, edit, contact, undo, or request-access behavior; unrecoverable states need a safe exit.

## Analytics And Experiment Coupling

- **Event taxonomy**: event name, schema, owner, compatibility rule, deprecated event mapping, and dashboard consumer must be named when instrumentation changes.
- **Exposure proof**: exposure event, assignment unit, de-duplication rule, conflict set, and eligibility filter must match the user-visible entry point.
- **Metric proof**: primary metric, guardrails, freshness, query/report owner, sample ratio mismatch check, and rollback threshold must be connected to the flow state that can affect them.
- **Dashboard migration**: old/new dashboard mapping, backfill need, freshness expectation, and stakeholder sign-off must be identified before removing or renaming events.
- **Not-enough-proof condition**: passing analytics events does not prove accessibility, content clarity, permission recovery, or breakpoint behavior.

## Graph, Memory, And Trajectory Coupling

- **Repository graph**: inspect existing route ownership, component boundaries, design-system primitives, content utilities, event taxonomy, permission wrappers, and shared state helpers before proposing placement.
- **Project memory**: check current requirements, prior decisions, acceptance criteria, regression history, and known UX constraints; mark memory stale when it predates the final product or code change.
- **Execution trajectory**: compare the proposed experience model with the latest diffs, test results, review comments, and validation runs; rerun or downgrade evidence when material files changed after validation.
- **Conflict handling**: when graph, memory, and current execution disagree, prefer current source and fresh validation, then record the stale artifact and next gate owner.
- **Efficiency rule**: reuse existing repository patterns before adding new structure; add a new component, event, or dependency only when the existing repository cannot satisfy the required behavior.

## Validation Evidence Patterns

- **State-to-validation map**: each state and accessibility obligation maps to a test, validator, manual walkthrough, screenshot, report, artifact, or explicit not-run risk.
- **Command evidence**: capture command, expected output, actual output summary, exit code, artifact/report path, and freshness after final material edit.
- **Visual evidence**: screenshots or recordings must identify viewport, browser, state, data condition, and whether they prove layout, focus, content, or only rendering.
- **Manual evidence**: keyboard and screen-reader checks must list the path walked, controls reached, announcements heard, and unsupported assistive technology combinations.
- **Evidence limits**: every closure states what evidence proves and what it does not prove about production data, browsers, breakpoints, accessibility tooling, analytics freshness, or release readiness.

## Anti-Patterns To Reject

- Modeling a modal or component without entry and exit graph.
- Treating a clean analytics report as proof that the user experience is accessible or recoverable.
- Accepting screenshots taken before the final copy, route, style, or data-state edit.
- Introducing a new dependency, component family, route owner, or event taxonomy without reuse and placement rationale.
- Reporting "tested" without command, validator, output, exit code, artifact, or not-run disclosure.
- Shipping an error state that clears recoverable input or offers no next action.

## Handoff Closure

Close the experience model with:
- Mode selected and why.
- Boundaries inspected and skipped with reason.
- Flow graph and state matrix.
- Accessibility and recovery obligations.
- Analytics, experiment, and dashboard impact.
- Reuse and placement rationale.
- Behavior preservation statement.
- State-to-validation map with fresh evidence.
- What evidence proves and what it does not prove.
- Residual risk, next gate, and owner.
