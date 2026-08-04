# Experience Output And Gates

Load this reference when `experience-impact-modeler` needs deeper experience proof than the body checklist can carry. Keep the Skill body compact; use this file for state-to-validation mapping, current-source freshness, analytics proof, and closure.

## Flow Evidence Matrix

| Dimension | Required Question | Evidence Pattern | Stop Condition |
|---|---|---|---|
| Actors and roles | Which user, account, tenant, permission, device, or assistive technology context enters the flow? | Actor table with role, entry point, permission state, and device context. | A role can reach the screen but has no modeled success, denial, or recovery path. |
| Entry and exit graph | Which routes, deep links, redirects, notifications, and back-navigation paths enter or leave the flow? | Route graph with entry, decision, completion, cancel, retry, and return paths. | The changed screen is modeled without upstream or downstream navigation. |
| State coverage | What does the user see for empty, loading, success, error, validation, disabled, permission-denied, timeout, partial success, cancel, and retry? | State table per screen or component with copy, focus, persistence, and recovery. | Any interactive element has an unowned state or vague "handle error" note. |
| Content and intent | Does copy explain what happened, what will happen, and how to recover? | Content delta table for labels, helper text, empty states, confirmations, and errors. | Copy is generic, ambiguous, or disconnected from the user's next action. |
| Responsive behavior | How does the flow change across mobile, tablet, desktop, hover, touch, and reduced-motion settings? | Breakpoint notes, overflow checks, target-size checks, and motion fallback. | The primary action, error, or recovery path becomes hidden or unreachable. |

## Accessibility And Recovery Gates

- **Keyboard path**: For each affected interactive or dynamic surface, state its applicable keyboard and focus behavior. Require trapping, Escape handling, route-change focus, and restoration only where its interaction model needs them.
- **Screen reader behavior**: For changed content or interaction semantics, record the applicable accessible-name, role, description, live-region, announcement-timing, and hidden or decorative-content obligations. If the change creates a plausible semantic or operability risk in an adjacent dimension that is skipped, record why.
- **Visual perception**: For changed visual content or interactions, record the applicable perceivability and operability obligations among contrast, non-color status, target size, text resize, reduced motion, and layout shift. If the change creates a plausible user risk in an adjacent dimension that is skipped, record why.
- **Input preservation**: Preserve affected user input only while it remains authorized, current, and safe to recover. Otherwise, record the concrete reason and recovery alternative.
- **Recovery path**: For an affected error classified recoverable, provide the recovery action allowed by product and security semantics—retry, cancel, edit, contact, undo, request access, or another owned path. For an unrecoverable state, provide a safe exit and terminal reason.

## Analytics And Experiment Coupling

- **Event taxonomy**: event name, schema, owner, compatibility rule, deprecated event mapping, and dashboard consumer must be named when instrumentation changes.
- **Exposure proof**: when a user-visible entry triggers analytics or experiment assignment, align the emitted exposure event and assignment unit with that entry path. The same alignment covers the de-duplication rule, conflict set, and eligibility filter. Record unobserved identity joins or channels.
- **Metric proof**: When analytics or an experiment is in scope, connect affected flow states to the selected primary metric and guardrails. Also connect data freshness and the query/report owner. Add sample-ratio-mismatch checks and rollback thresholds when assignment or release decisions use them.
- **Dashboard migration**: before an instrumentation change removes or renames an event, identify the affected old/new dashboard mapping, backfill need, freshness expectation, and stakeholder sign-off.
- **Not-enough-proof condition**: passing analytics events does not prove accessibility, content clarity, permission recovery, or breakpoint behavior.

## Current Evidence And Freshness

- **repository inspection**: inspect existing route ownership, component boundaries, design-system primitives, content utilities, event taxonomy, permission wrappers, and shared state helpers before proposing placement.
- **Prior task evidence**: check current requirements, prior decisions, acceptance criteria, regression history, and known UX constraints; mark a prior claim stale when it predates the final product or code change.
- **Observable action sequence**: compare the proposed experience model with the latest diffs, test results, review comments, and validation runs; rerun or downgrade evidence when material files changed after validation.
- **Conflict handling**: when repository inspection, prior task evidence, and the latest diff disagree, prefer current source and fresh validation, then record the stale artifact and recommended next step owner.
- **Efficiency rule**: reuse existing repository patterns before adding new structure; add a new component, event, or dependency only when the existing repository cannot satisfy the required behavior.

## Validation Evidence Patterns

- **State-to-validation map**: each state and accessibility obligation maps to a test, validator, manual walkthrough, screenshot, report, artifact, or explicit not-run risk.
- **Command evidence**: capture command, expected output, actual output summary, exit code, artifact/report path, and freshness after final material edit.
- **Visual evidence**: when screenshots or recordings support an experience claim, identify viewport, browser, state, data condition, and whether they prove layout, focus, content, or rendering alone.
- **Manual evidence**: when keyboard or screen-reader checks support experience closure, record the path walked, controls reached, announcements heard, and unsupported assistive-technology combinations.
- **Evidence limits**: For the affected flow and inspected states, state what the selected evidence proves and identify material untested production-data, browser, breakpoint, accessibility-tooling, analytics-freshness, or release-readiness limits.

## Anti-Patterns To Reject

- Modeling a modal or component without entry and exit graph.
- Treating a clean analytics report as proof that the user experience is accessible or recoverable.
- Accepting screenshots taken before the final copy, route, style, or data-state edit.
- Introducing a new dependency, component family, route owner, or event taxonomy without reuse and placement rationale.
- Reporting "tested" without command, validator, output, exit code, artifact, or not-run disclosure.
- Shipping an error state that clears recoverable input or offers no next action.

## Handoff Closure

Close with the selected mode, inspected and skipped boundaries, flow and state models, and accessibility, recovery, analytics, reuse, placement, and behavior-preservation obligations. Include fresh state-to-validation evidence and its limits, residual risk, next step, and owner.
