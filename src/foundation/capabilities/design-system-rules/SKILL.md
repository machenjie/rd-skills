---
name: design-system-rules
description: Applies component consistency, reuse, accessibility, responsive behavior, variant control, and justification rules for introducing new UI components.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "11"
changeforge_version: 0.1.0
---

# Mission

Govern every frontend UI change against the product design system to guarantee **component reuse, controlled variation, accessibility compliance (WCAG 2.2 AA), responsive completeness, and long-term component library maintainability** — so new work extends the system rather than fragmenting it.

# When To Use

Use this capability when a frontend change: selects an existing component or creates a new one; chooses variants, sizes, color tokens, spacing scales, or typography roles; defines responsive layout breakpoints or adaptive behaviors; implements form patterns, validation states, loading states, empty states, or error states; specifies focus behavior, keyboard navigation, or screen reader announcements; applies icons, illustrations, or motion; introduces a new design token or overrides an existing one.

# Do Not Use When

Do not use this capability to design or architect a new design system from scratch (that is product-level architecture work requiring dedicated design leadership). Do not use it to justify purely decorative changes where no component or interaction decision is being made. Do not use it when the UI intent is not yet defined — use `prototype-description` first.

# Stage Fit

Use during experience-definition, implementation-planning, coding, and review when component choice, token use, variant governance, accessibility semantics, or responsive behavior can fragment the product UI. In planning, it defines the component and token contract before implementation. In coding/review, it rejects drift from current design-system source, stale project memory, copied patterns without graph confirmation, and accessibility/responsive claims without validation evidence. Hand off when the primary question is page structure, state transitions, API lifecycle, or executable frontend tests.

# Non-Negotiable Rules

- **Reuse existing components and variants first.** A new component is only justified when: (1) the interaction semantics genuinely differ from all existing components; (2) the need will recur in at least 3 distinct product surfaces; (3) a reuse owner and documentation plan are identified. Custom one-off styling is not a justification for a new primitive.
- **Accessibility is non-negotiable from first implementation.** WCAG 2.2 Level AA is the minimum. Criteria that cannot be retrofitted: 1.4.11 Non-text Contrast (≥ 3:1 for UI components), 1.4.3 Text Contrast (≥ 4.5:1), 2.4.7 Focus Visible, 2.5.8 Target Size Minimum (24×24 CSS px), 4.1.2 Name/Role/Value (ARIA semantics). Never defer accessibility to a separate "accessibility pass."
- **Variants encode product states, not visual preferences.** Allowed variant axes: `intent` (primary/secondary/danger/warning/success/info), `size` (sm/md/lg), `density` (default/compact), `state` (default/hover/active/disabled/loading/error). Forbidden: ad hoc color overrides, unsanctioned font-size props, inline style overrides to satisfy one screen's design.
- **Design tokens are the only sanctioned styling mechanism.** Direct hex codes, hardcoded px values, and font family strings in component code are violations. Use only design-system–exported tokens: `color.*`, `space.*`, `typography.*`, `radius.*`, `shadow.*`, `motion.*`.
- **Responsive rules cover the full task, not just the viewport.** For each responsive state (mobile, tablet, desktop, wide): primary action must be reachable, text must not overflow or become unreadable, touch targets must meet 44×44 CSS px (WCAG 2.5.5 AAA) or 24×24 minimum (2.5.8 AA), form fields must remain operable, data tables must have a defined overflow strategy (scroll, collapse, or summarize).
- **Focus management is explicit for dynamic content.** When a modal, drawer, toast, or popover opens, focus must move to the first focusable element or the container. When it closes, focus must return to the trigger. Dialogs must trap focus. `aria-live` regions must be declared for async state updates.
- **Component API stability is a compatibility contract.** Once a component is released to the design system, removing a prop or changing its semantics is a breaking change. Additions are non-breaking. Deprecation requires a migration path and a minimum 2-sprint notice.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Existing component selection | UI can be built from current primitives or patterns. | Reuse exact components, slots, variants, and state treatments. | Current design-system source/story/docs, accepted component, rejected alternatives. | `page-component-decomposition`, `frontend-testing` | New component proposal. |
| Variant or token decision | New variant, token, density, theme, icon, motion, spacing, or typography choice. | Keep axes product-state-driven and tokenized. | Axis/value, token source, state coverage, contrast proof. | `interaction-state-modeling`, `frontend-testing` | Raw CSS or one-off overrides. |
| Accessibility-critical UI | Modal, menu, combobox, data grid, form error, disabled action, live update, or keyboard path. | Name/role/value, focus, target size, live regions, contrast, reduced motion. | WCAG SC list, keyboard path, axe/manual coverage, unresolved specialist review. | `interaction-state-modeling`, `security-privacy-gate` when permission copy leaks | Accessibility as a later pass. |
| Responsive or dense surface | Mobile/tablet/desktop/wide layout, data table, sticky action, overflow, truncation, or compact density. | Preserve task completion and readability at each breakpoint. | Breakpoint map, overflow strategy, touch target, text wrapping/truncation rule. | `prototype-description`, `frontend-testing` | Desktop-only design proof. |
| New component proposal | Existing primitives cannot express semantics and reuse pressure is real. | Govern API, ownership, stories, docs, deprecation, and reuse criteria. | ≥ 3 surfaces or approved exception, owner, API, a11y spec, Storybook/test plan. | `implementation-structure-design`, `page-component-decomposition` | Future hypothetical reuse. |

# Industry Benchmarks

Anchor against WCAG 2.2 AA, WAI-ARIA 1.2/APG, APCA readiness, Material Design 3, Apple HIG, Fluent 2, Spectrum, axe-core, Storybook accessibility checks, Lighthouse accessibility scoring, ISO 9241-171, and Section 508. Keep this body focused on routing, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for component decision trees, variant matrices, WCAG criterion detail, responsive checklists, and proposal evidence packs.

# Selection Rules

Select this capability when **component choice, variant governance, accessibility requirements, or responsive behavior** are primary design decisions. Adjacent routing:

- Prefer `prototype-description` when the UI interaction intent is not yet decided.
- Prefer `information-architecture` when navigation structure and content hierarchy are primary.
- Prefer `routing-navigation-design` when URL routing and screen transitions are primary.
- Prefer `form-validation-design` when form input validation semantics are the focus.
- Prefer `frontend-change-builder` for implementation execution after design decisions are made.
- Prefer `frontend-testing` when visual regression, accessibility, and cross-browser coverage are the focus.

# Proactive Professional Triggers

- **Signal:** a UI change names no current design-system component, story, token source, or rejected alternative. **Hidden risk:** engineers create one-off UI from memory or screenshots. **Required professional action:** inspect current component docs/source before approving implementation. **Route to:** `repository-context-map`, `page-component-decomposition`. **Evidence required:** accepted component, rejected closest alternatives, source freshness.
- **Signal:** a new prop, variant, token, class, icon treatment, or density setting is added for one screen. **Hidden risk:** variant proliferation and theme/accessibility drift. **Required professional action:** prove product-state axis, reuse pressure, owner, and Storybook/test coverage. **Route to:** `implementation-structure-design`, `frontend-testing`. **Evidence required:** axis/value rationale, invalid combinations, consumers, compatibility note.
- **Signal:** accessibility is described generically as "use ARIA", "make accessible", or "run axe" without component-specific criteria. **Hidden risk:** keyboard, focus, status, and name/role/value defects survive automation. **Required professional action:** map WCAG SC and ARIA/APG obligations to each interactive state. **Route to:** `interaction-state-modeling`, `quality-test-gate`. **Evidence required:** keyboard path, focus behavior, live regions, manual gaps.
- **Signal:** responsive behavior is verified only at a desktop viewport or by visual fit. **Hidden risk:** primary task, text, overflow, or touch targets fail on mobile/dense contexts. **Required professional action:** define breakpoint behavior and overflow/truncation policy. **Route to:** `prototype-description`, `frontend-testing`. **Evidence required:** mobile/tablet/desktop/wide map and residual device risk.
- **Signal:** project memory, repository graph, or prior agent trajectory suggests a component pattern. **Hidden risk:** stale or locally-specialized UI pattern is copied into the wrong surface. **Required professional action:** current-source-confirm reuse before trusting memory. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected files/stories/tests, accepted or rejected pattern, freshness limit.

# Risk Escalation Rules

Escalate when: a new component primitive is proposed (governance review required); keyboard or focus patterns change from established product standard; a variant addition could cause existing states to become unreachable or invisible; accessible contrast fails in both light and dark themes; a change affects mobile native semantics (iOS `UIKit` / Android `Compose`) where ARIA patterns do not apply; a design token is proposed to be removed or renamed (breaking change); responsive behavior hides an action that is the only path to complete a user task.

# Critical Details

Design systems accumulate technical and visual debt at the component level. Precision failures:

- **Variant proliferation.** Every `isSpecialCase: boolean` prop added to a shared component adds two paths to maintain, test, and document. After 10 such props, combinatorial state testing becomes impractical. Govern variants strictly; reject novelty props that serve one screen.
- **Color token bypass.** A hex code hardcoded in a component breaks dark mode, theming, and the ability to update brand colors system-wide. `color.action.primary` is not `#0052CC` — the token is; the hex is an implementation detail of the current theme.
- **Focus trap bugs.** Modal dialogs that do not trap focus allow screen reader users to reach content behind the overlay. Focus trap is not a progressive enhancement — it is required by WCAG SC 2.1.2 (No Keyboard Trap) and the ARIA Dialog Pattern.
- **Loading state omission.** When an async action fires but no loading state is shown, users double-click, submit multiple times, or assume failure. Every async action requires: a loading state that disables the trigger and communicates progress.
- **Empty state neglect.** Tables, lists, and data grids without empty state templates show jarring blank screens. Every data surface needs: empty state with explanation and a primary action to resolve it.
- **Touch target clustering.** Icon buttons in tight rows on mobile — delete, edit, share in a 32px-tall row — are impossible to hit reliably. Test with 44px minimum target size on physical devices, not just browser DevTools.
- **Animation without prefers-reduced-motion.** Decorative animation that plays unconditionally can trigger vestibular disorders. Every animation must respond to `@media (prefers-reduced-motion: reduce)`.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 design-system selection, governance, and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete component/variant/token decision, accessibility requirement, responsive rule, or new component proposal. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when benchmark detail, WCAG criteria, component selection trees, variant matrices, responsive checklists, or proposal evidence packs are needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| `<Button color="#e53935">Delete</Button>` | Token bypass; breaks theming; dark-mode inaccessible |
| New `<DashboardCard>` component for one dashboard screen | No reuse; duplicates `<Card>` primitive; no owner |
| `disabled` prop on a form element without `aria-disabled` | Screen readers do not announce disabled state on some browsers |
| Responsive layout tested only at 1280px | Mobile tasks may be impossible; WCAG 1.3.4 (Orientation) not checked |
| Loading state: spinner overlay without disabling the submit button | Double-submit; multiple API requests; race condition |
| `role="button"` on a `<div>` without `tabIndex="0"` | Not keyboard focusable; SC 2.1.1 Keyboard violation |
| Error state color only (red border, no text) | SC 1.4.1 Use of Color violation; color-blind users cannot detect error |
| `aria-label` set to icon name instead of action name | "pencil" vs "Edit profile" — icon name is not an action label |

# Failure Modes

- One-off component introduced for a single screen duplicates an existing pattern; proliferates to 12 variants; no owner; becomes unmaintained.
- Hard-coded hex color bypasses token system; dark mode fails with low contrast ratio 1.8:1; WCAG violation.
- Focus not trapped in modal; keyboard users can reach background page controls; screen reader users confused.
- `aria-live` region missing on async search results; screen reader users do not learn that results have updated.
- Touch target 20×20 CSS px on mobile action buttons; error rate in usability testing > 30%.
- Variant prop explosion: Button has 14 boolean modifiers; combinatorial test matrix exceeds 16,384 states; not tested.
- Animation without `prefers-reduced-motion`; vestibular disorder complaint; accessibility legal notice issued.
- Design token renamed in minor version; all consumer teams' builds break with undefined token value.
- Empty state not implemented; data table shows blank screen after filter returns zero results; users assume bug.
- Form labels implemented visually with placeholder text only; screen reader reads "Edit text" instead of field purpose.

# Output Contract

Return design-system rules with:

- `mode_selected` (existing component selection / variant-token decision / accessibility-critical UI / responsive-dense surface / new component proposal)
- `source_evidence` (current design-system docs/source/stories, component consumers, tokens, tests, repository graph, project memory, or execution trajectory inspected with freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each remembered/reused pattern)
- `components_to_use` (exact names from design system; links to Storybook stories)
- `variants_required` (axis + value pairs; justification if non-standard)
- `variants_forbidden` (list of disallowed prop combinations for this use case)
- `accessibility_requirements` (WCAG criteria per SC number; ARIA roles/properties; keyboard navigation pattern; focus management spec)
- `responsive_behavior` (per breakpoint: layout strategy, action visibility, overflow handling)
- `tokens_used` (list of design tokens; confirm no raw hex/px values)
- `motion_behavior` (`prefers-reduced-motion` compliance; animation purpose)
- `new_component_justification` (if applicable: reuse need, interaction difference, API design, owner, Storybook/docs/deprecation plan)
- `test_requirements` (axe-core, Lighthouse, keyboard navigation, screen reader, cross-browser)
- `changed_design_system_to_validation_map` (each component, variant, token, state, responsive rule, a11y obligation, and new-component decision mapped to validation or residual risk)
- `handoff_boundaries` (what belongs to prototype, interaction states, page decomposition, implementation, frontend tests, specialist accessibility, or design leadership)
- `review_evidence` (screenshots or stories of all states, contrast check results, WCAG checklist completion, command output or not-verified disclosure)
- `evidence_limits` (what was not inspected or not run: real design-system docs, browser render, physical device, screen reader, Storybook, axe, Lighthouse, or cross-browser)

# Evidence Contract

Close a design-system-rules change only when the output names selected mode, current source evidence inspected, graph/memory/trajectory reuse judgment, accepted components and rejected alternatives, variant/token decisions, accessibility and responsive obligations, new-component justification or rejection, changed-design-system-to-validation map, handoff boundaries, residual risk, and evidence limits. A generic "follow the design system" or "run accessibility checks" statement is not sufficient evidence.

# Benchmark Coverage

Improved design-system reviews reject common weak patterns: one-off components, raw colors/spacing, visual preference variants, desktop-only verification, ARIA without keyboard behavior, color-only error states, spinner-only async states, and undocumented breaking token/prop changes. Detailed benchmark anchors, WCAG matrices, variant axis tables, and responsive checklists belong in references so the body stays efficient.

# Routing Coverage

Route here when component governance, design tokens, variants, responsive behavior, accessibility semantics, or new component justification is primary. Hand off when the primary concern is screen intent (`prototype-description`), content/navigation hierarchy (`information-architecture`), component ownership (`page-component-decomposition`), state transitions (`interaction-state-modeling`), data fetching lifecycle (`frontend-api-integration`), or executable tests (`frontend-testing` / `quality-test-gate`).

# Quality Gate

The design-system rules review passes only when:

1. No new component introduced without reuse evidence (≥ 3 surfaces) and governance approval.
2. All variants map to sanctioned axes; no ad hoc color or size overrides.
3. All tokens are from the design-system export; no hardcoded hex, px, or font values in component code.
4. WCAG 2.2 AA checklist completed; automated axe-core scan passes with 0 violations.
5. Contrast ratios documented for text (≥ 4.5:1) and UI components (≥ 3:1) in both themes.
6. Focus behavior specified for all dynamic content; modal focus trap confirmed.
7. Responsive behavior documented for mobile, tablet, desktop; touch targets ≥ 24×24 CSS px.
8. Loading, empty, error, and disabled states designed for every interactive surface.
9. `prefers-reduced-motion` compliance declared for any animation.
10. Storybook story exists (or is planned) for each new variant or component.
11. Selected mode, source evidence, and rejected component/variant alternatives are explicit.
12. Repository graph, project memory, and execution trajectory inputs are current-source-confirmed or marked not verified.
13. Every changed component, variant, token, state, breakpoint, accessibility obligation, and new-component decision maps to validation evidence or named residual risk.
14. Handoff boundaries and evidence limits are named so design-system review is not over-claimed as implementation, browser/device testing, or full accessibility certification.

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `frontend-change-builder` for implementation; `frontend-testing` for visual regression, Lighthouse, and cross-browser coverage; `prototype-description` when interaction intent needs further definition; specialist accessibility review when ARIA patterns involve complex composite widgets (data grid, combobox, tree).

# Completion Criteria

The capability is complete when every UI component choice, variant, token, accessibility requirement, and responsive behavior is **governed by design-system rules** — with no hardcoded values, no unjustified new primitives, no unresolved WCAG violations, and all interactive states designed before implementation begins.
