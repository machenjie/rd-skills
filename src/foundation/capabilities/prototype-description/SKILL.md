---
name: prototype-description
description: Describes UI intent, layout hierarchy, interaction contract, validation, and state behavior without over-specifying visual design.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "09"
changeforge_version: 0.1.0
---

# Mission

**Translate product and experience intent into a prototype brief that defines layout hierarchy, interaction contract, validation behavior, state obligations, and accessibility requirements** — giving implementers enough specificity to build a professional, consistent, accessible experience without requiring a full design file, while leaving visual execution to the existing design system rather than reinventing it.

# When To Use

Use this capability when: a UI change needs a concise description of layout hierarchy, content priority, and interaction behavior before implementation begins; a new feature surface is being introduced and implementers need to understand the information architecture before choosing components; a multi-step workflow, form, or data entry surface requires explicit validation timing and error state definitions; accessibility obligations for a new interaction pattern need to be captured before the component is built; or product intent exists (user stories, acceptance criteria) but the implementation team needs a concrete UI specification to build consistently against.

# Do Not Use When

Do not use this capability to: create pixel-perfect visual specifications (spacing values, exact color codes, border radii — these belong in the design system); introduce a new visual language or component pattern without a design system review; specify an interaction that duplicates an existing design system component without justification; replace a full design system prototype or Figma file when one exists; or document purely back-end or API behavior with no user-facing surface.

# Stage Fit

Use during experience-definition and implementation-planning when the team needs enough UI behavior to build consistently but does not yet need a full component decomposition or visual spec. In coding, bug-fix, debugging, code-review, refactoring, and testing, use the brief as the contract for hierarchy, actions, validation, state obligations, accessibility, and reuse. Hand off, rather than expand this body, when the work becomes navigation architecture, detailed state-machine design, design-system governance, frontend implementation, or release readiness.

# Non-Negotiable Rules

- **Describe intent and hierarchy — not visual decoration.** The brief answers: what does the user need to see and do on this surface? It does not answer: what shade of blue is the button? Visual decisions belong to the design system. Implementers who receive a brief that mixes interaction intent with specific CSS values will either ignore the CSS (wasted effort) or over-customize components (design system drift).
- **Content priority must reflect user decision order, not implementation convenience.** Users read and decide top-to-bottom, primary-to-secondary. The hierarchy should be: primary message or action at the top; supporting information in the middle; secondary and destructive actions last. A form that leads with 12 optional fields before the required primary field follows database column order, not user decision flow. The brief must explicitly state the priority ordering.
- **Validation behavior must define: when validation runs, where errors appear, and what happens to user input.** Three timing models: (1) On submit — validate all fields at once on form submission; reveal all errors simultaneously. (2) On blur — validate each field when it loses focus; show error immediately after leaving the field. (3) On change — validate in real time as the user types (use sparingly — on-change for format masks like phone number; not for business logic that requires a server round-trip). Error placement: inline below the field, not in a banner at the top of the page (unless the error is cross-field or system-level). User input must be preserved — never clear the form on validation failure.
- **Every interactive state must be defined.** For each interactive surface (form, list, button group, data table, step-by-step wizard): idle (default loaded state), loading (async operation in progress — what is shown?), empty (no data — empty state with action or explanation), error (system or network failure — what is shown, what can the user do?), disabled (when is each action disabled, and why?), success (confirmation that an action completed). Missing state definitions create inconsistent UX and untestable components.
- **Accessibility obligations must be stated, not assumed.** For every new interactive pattern: keyboard navigation order (Tab sequence; do modal dialogs trap focus?); screen reader role and label (`role="dialog"`, `aria-labelledby`, `aria-describedby`); focus management (where does focus go after a modal opens? after a form submits? after a list item is deleted?); color is not the only differentiator for meaning (error states must include icon or text label, not only a red border — WCAG 1.4.1 Use of Color). The brief does not need to specify ARIA implementation details — it must state what the accessibility behavior should be.
- **Reuse expectations must be explicit.** For every component referenced in the brief: "use existing `<DataTable>` component from design system" vs. "this pattern does not exist in the design system — new component required." New component proposals must include the reuse justification (who else will use it?) and trigger a design-system-rules review before implementation.
- **Prototype scope must be bounded.** A brief names unresolved product/design/technical decisions; it must not pretend to settle unknown copy, permission policy, backend error semantics, or component API details that require another owner.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Surface brief | One screen, panel, modal, or drawer needs buildable UI intent. | Hierarchy, regions, actions, validation, states, accessibility, reuse. | Surface, user goal, trigger, priority order, state obligations. | `information-architecture`, `design-system-rules` | Full journey map. |
| Form or data-entry brief | Required fields, validation timing, server validation, destructive/cancel actions. | Input preservation, field/system errors, submit/loading/success behavior. | Validation timing, error placement, preserved input, recovery path. | `form-validation-design`, `interaction-state-modeling` | Pixel layout or CSS rules. |
| Async/list/table brief | Data table, search, filter, export, import, background job, empty state. | Loading/empty/error/success definitions and safe retry/download behavior. | Empty copy/action, loading treatment, retry safety, completion signal. | `interaction-state-modeling`, `frontend-api-integration` | Backend job implementation. |
| New pattern candidate | Existing design-system component may not fit. | Reuse proof before proposing new component or variant. | Existing component inspected, gap, recurrence signal, review owner. | `design-system-rules`, `page-component-decomposition` | One-off custom component. |
| Flow handoff brief | A single surface sits inside a multi-step flow. | Local screen contract plus handoff to ordered flow/state design. | Entry/exit context, back/cancel behavior, partial-progress risk. | `user-flow-modeling`, `routing-navigation-design` | Complete flow model in this brief. |
| Accessibility-critical brief | Modal, keyboard-heavy widget, destructive action, sensitive form, regulated data. | Focus, keyboard, announcements, error identification, color independence. | Keyboard order, focus target, live region/role need, WCAG risk. | `frontend-testing`, `security-privacy-gate` when sensitive data appears | Accessibility "later" pass. |

# Proactive Professional Triggers

- **Signal:** A request says "mock up", "prototype", or "make a screen" but names only visual style. **Hidden risk:** implementation guesses task priority, state behavior, and accessibility. **Required professional action:** produce a prototype brief before component work. **Route to:** `prototype-description`, `information-architecture`. **Evidence required:** user goal, hierarchy, actions, states, accessibility obligations.
- **Signal:** A brief lists content regions but no loading, empty, error, disabled, or success behavior. **Hidden risk:** blank screens, misleading success, and untestable UI states. **Required professional action:** add state obligations or hand off detailed state matrix. **Route to:** `interaction-state-modeling`, `frontend-testing`. **Evidence required:** state list, recovery action, test obligation.
- **Signal:** A form or destructive action lacks validation timing, input preservation, confirmation, or consequence copy. **Hidden risk:** data loss, accidental destructive action, inaccessible error recovery. **Required professional action:** define the interaction contract before implementation. **Route to:** `form-validation-design`, `user-flow-modeling`. **Evidence required:** timing, error placement, confirmation mechanism, preservation rule.
- **Signal:** The brief proposes a new component, custom control, or "whatever component fits" without reuse evidence. **Hidden risk:** design-system drift and duplicate inaccessible patterns. **Required professional action:** inspect existing patterns and escalate new pattern governance. **Route to:** `design-system-rules`, `implementation-structure-design`. **Evidence required:** reuse candidate, gap, recurrence/owner, review requirement.
- **Signal:** Accessibility is described only as "accessible" or color is the only error/success signal. **Hidden risk:** keyboard and screen-reader users cannot complete the task. **Required professional action:** state focus, keyboard, role/label/live-region, and color-independent feedback. **Route to:** `frontend-testing`, `design-system-rules`. **Evidence required:** accessible behavior contract and WCAG-related test expectation.
- **Signal:** The prototype brief crosses multiple pages, deep links, permission branches, or re-entry paths. **Hidden risk:** the brief hides a flow problem inside a screen spec. **Required professional action:** keep local surface scope and hand off full journey to flow/routing capabilities. **Route to:** `user-flow-modeling`, `routing-navigation-design`. **Evidence required:** local entry/exit context and handoff boundary.

# Industry Benchmarks

Anchor against WCAG 2.2 structure, keyboard, focus order, error identification, labels, and error-prevention criteria; Nielsen visibility/error-recovery heuristics; form validation timing research; Atomic Design vocabulary; platform HIG conventions; and ARIA APG patterns for dialogs and composite widgets. Keep the root body limited to routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for state coverage aids, prototype brief templates, benchmark detail, and anti-pattern review.

# Selection Rules

Select this capability when implementers need **UI intent precise enough to build a professional experience without a full design file**. Route elsewhere when: **design-system-rules** is primary (which existing components to use, how to extend the design system, variant governance); **interaction-state-modeling** is primary (detailed state machine design for a complex interactive flow — e.g., a multi-step checkout with 12 distinct states and branching logic); **page-component-decomposition** is primary (which React/Vue components own which responsibilities on an already-understood page); **user-flow-modeling** is primary (mapping the complete journey across multiple pages, not specifying the UI behavior of one surface).

# Risk Escalation Rules

Escalate when: the brief introduces a new component pattern not present in the design system (requires design-system-rules review and approved design before implementation); a change affects a critical data entry path (financial transactions, medical data entry, legal documents — accessibility must be explicitly reviewed, not assumed); the interaction requires conveying important information through color alone (accessibility violation — WCAG 1.4.1); a new form collects sensitive user data (PII, financial data) and data handling behavior is not yet defined; or the prototype description conflicts with an existing user flow (e.g., introduces a second path to the same action that contradicts the primary navigation model).

# Critical Details

- **Empty states are as important as the populated state.** A dashboard showing "no data yet" for a new user is the user's first impression of the product. An empty state with no guidance, no call to action, and no explanation of why there is no data is a UX failure. The brief must define: what is shown when the list/table/chart has zero records; whether there is a primary action to create the first record; what copy explains the empty condition.
- **Destructive actions require confirmation and must be visually separated.** "Delete account", "Cancel subscription", "Discard draft" — destructive actions must not be adjacent to primary actions (accidental clicks), must use a confirmation dialog or inline confirmation step, and must state the consequence clearly ("This will permanently delete 47 orders and cannot be undone"). The brief must specify the confirmation mechanism and the consequence copy — not just "confirm before delete."
- **Loading states must be designed, not inferred.** "Show a spinner" is not a loading state design. The brief must specify: what exactly is shown while loading (skeleton UI vs spinner vs blank page); whether partial data can be shown while the rest loads; what happens if loading takes > 5 seconds (timeout message, retry action); whether the page is interactive during loading (can the user navigate away safely?). Loading state omissions are the most common cause of blank screens in production.
- **Prototype briefs are owned by product, reviewed by UX, and implemented by engineering.** A brief written by engineering without product input may optimize for implementation convenience rather than user decision flow. A brief written by product without engineering review may propose interactions that are impossible with the current component system. The brief is a collaboration artifact, not a unilateral specification.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 prototype-brief rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a real brief, when accessibility/destructive/action-state evidence is uncertain, or when the brief must be checked before implementation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when benchmark detail, state coverage aids, the reusable brief template, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording changes where the output contract and quality gate are sufficient.

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| "Show a red border on error" — no error text, no icon | Color-only error indication; WCAG 1.4.1 violation; screen reader cannot perceive the error | "Show red border + error icon + inline error text below field" |
| Form clears all fields on submit failure | User loses entered data; extremely frustrating for long forms | Preserve all field values on validation failure; highlight only failing fields |
| Brief describes 12 interactions but no empty state | New users see blank UI with no guidance; conversion fails | Define empty state: copy + primary action CTA for every list, table, and dashboard surface |
| "Delete button at top right next to Save" | Destructive action adjacent to primary action; accidental deletions | Move destructive action to bottom-left or separate it visually; require confirmation |
| Loading state: "show spinner" | Unspecified: where? how large? does it block the page? can user navigate? | Specify skeleton or spinner placement, whether page is interactive, and timeout behavior |
| "Use whatever component makes sense" | No reuse direction; engineers choose different components for the same pattern; inconsistent UX | Explicit component reference: "use existing `<Modal>` from design system; trigger design-system-rules review if insufficient" |

# Failure Modes

- **Blank first-run list:** implementation ships with no empty state on a data list, so new users see a blank page with no explanation or next action.
- **Color-only error:** error state for a payment form shows only a red border; screen reader users cannot identify which field failed.
- **Input loss on validation:** a 20-field form clears after server validation fails; the user cannot recover and abandons the task.
- **Inaccessible delete confirmation:** destructive action uses `window.confirm()`, blocking thread, hiding focus behavior, and bypassing design-system dialog semantics.
- **Ambiguous loading:** loading state is absent or spinner-only, so users see a blank page, double-submit, or navigate away before completion.
- **Duplicate component drift:** a custom date picker duplicates the design-system date picker with different keyboard behavior and no owner.
- **Flow hidden in a screen brief:** a single-surface prototype silently includes deep links, back behavior, partial progress, and permission branches that require flow/routing design.
- **Evidence overclaim:** a brief says "accessible and reusable" without inspected component evidence, review artifact, or residual risk, so implementation treats assumptions as approved design.

# Output Contract

Return a prototype brief with:

- `mode_selected` (surface brief / form or data-entry / async list-table / new pattern candidate / flow handoff / accessibility-critical)
- `source_evidence` (product intent, current surface/flow/pattern evidence, design-system components inspected, graph/memory/trajectory signals used or rejected, and freshness limits)
- `surface` (name; user goal; trigger / how user arrives)
- `information_hierarchy` (ordered list: most important → least important; justified by user decision order)
- `layout_regions` (page/panel/modal/drawer/inline regions; purpose and relationship, not pixel placement)
- `actions` (primary action: label + result; secondary actions; destructive action: label + confirmation + consequence copy)
- `interaction_contract` (submit/edit/confirm/cancel/retry/undo behavior; what persists; what is reversible)
- `validation` (per field: rule, error message, placement; timing: on-submit/on-blur/on-change; input preservation guarantee)
- `states` (idle, loading, empty, error: field and system, disabled conditions, success)
- `accessibility` (keyboard nav order; focus management; screen reader role + label; color independence confirmation)
- `design_system_reuse` (per referenced component: existing / extend / new + justification)
- `handoff_boundaries` (what belongs to flow modeling, state modeling, design-system review, frontend implementation, or product/design decision)
- `changed_prototype_to_validation_map` (each hierarchy, action, validation rule, state, accessibility obligation, reuse decision, and open decision mapped to test/review evidence or residual risk)
- `evidence_limits` (what was not inspected or not run: design source, live render, browser/mobile behavior, screen reader, component docs, analytics, or user research)
- `open_decisions` (unresolved product, design, or technical questions blocking implementation)

# Evidence Contract

Close a prototype-description change only when the output names selected mode, boundaries inspected, product/user-flow/context evidence, source design-system or pattern reuse evidence, state/accessibility obligations, changed-prototype-to-validation map, validation command or review artifact with exit code/report path when available, what evidence proves and does not prove, behavior preservation, residual risk, unresolved product/design/technical decisions, and the handoff or next gate owner. A visual-only mockup description or generic "make it accessible" statement is not sufficient evidence.

# Benchmark Coverage

Behavior improvement should be validated structurally: baseline weak briefs usually over-specify visuals, omit states, or leave reuse/accessibility implicit; treatment briefs must name mode, source evidence, hierarchy, action contract, state obligations, accessibility, reuse, validation map, evidence limits, and handoff limits. Token/turn overhead is acceptable only while the brief remains shorter than a full interaction-state matrix or design-system spec.

# Routing Coverage

Route here for screen-level UI intent. Guard against over-routing by handing off when the primary work is full journey mapping (`user-flow-modeling`), detailed state transitions (`interaction-state-modeling`), component API/variant governance (`design-system-rules`), component implementation ownership (`page-component-decomposition` / `frontend-change-builder`), or backend/API behavior with no visible surface.

# Quality Gate

The brief is complete only when:

1. Information hierarchy reflects user decision order — not implementation order.
2. All six required states are defined: idle, loading, empty, error (field), error (system), success.
3. Validation defines timing, error placement, and input preservation.
4. Destructive actions have a specified confirmation mechanism and consequence copy.
5. Accessibility: keyboard nav, focus management, and color independence stated.
6. Every referenced component is explicitly: use existing / extend / new.
7. New component proposals are flagged for design-system-rules review.
8. Empty states include copy and available next action.
9. Loading states specify what is shown and whether the page is interactive during load.
10. No visual decoration specified (no colors, spacing, or font sizes) — only interaction intent.
11. The selected mode and handoff boundaries are explicit.
12. Existing component/pattern reuse was inspected before a new component or variant is proposed.
13. Open decisions are named with owner and whether they block implementation.
14. The brief states what test, validator, review artifact, or report should prove the interaction contract, including exit code when a command was run.
15. Evidence limits and residual risk are explicit; a prototype brief is not over-claimed as a visual design, accessibility certification, or frontend implementation.

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `design-system-rules` for component selection and new component governance; `interaction-state-modeling` for detailed state machine design for complex multi-step flows; `page-component-decomposition` for component responsibility mapping; `frontend-testing` for test strategy based on the defined states.

# Completion Criteria

The capability is complete when **UI intent is specific enough that two engineers would produce consistent implementations independently, every interactive state is defined, accessibility obligations are stated, and visual execution is fully delegated to the design system**.
