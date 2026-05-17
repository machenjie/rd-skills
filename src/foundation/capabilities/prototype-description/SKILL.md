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

# Non-Negotiable Rules

- **Describe intent and hierarchy — not visual decoration.** The brief answers: what does the user need to see and do on this surface? It does not answer: what shade of blue is the button? Visual decisions belong to the design system. Implementers who receive a brief that mixes interaction intent with specific CSS values will either ignore the CSS (wasted effort) or over-customize components (design system drift).
- **Content priority must reflect user decision order, not implementation convenience.** Users read and decide top-to-bottom, primary-to-secondary. The hierarchy should be: primary message or action at the top; supporting information in the middle; secondary and destructive actions last. A form that leads with 12 optional fields before the required primary field follows database column order, not user decision flow. The brief must explicitly state the priority ordering.
- **Validation behavior must define: when validation runs, where errors appear, and what happens to user input.** Three timing models: (1) On submit — validate all fields at once on form submission; reveal all errors simultaneously. (2) On blur — validate each field when it loses focus; show error immediately after leaving the field. (3) On change — validate in real time as the user types (use sparingly — on-change for format masks like phone number; not for business logic that requires a server round-trip). Error placement: inline below the field, not in a banner at the top of the page (unless the error is cross-field or system-level). User input must be preserved — never clear the form on validation failure.
- **Every interactive state must be defined.** For each interactive surface (form, list, button group, data table, step-by-step wizard): idle (default loaded state), loading (async operation in progress — what is shown?), empty (no data — empty state with action or explanation), error (system or network failure — what is shown, what can the user do?), disabled (when is each action disabled, and why?), success (confirmation that an action completed). Missing state definitions create inconsistent UX and untestable components.
- **Accessibility obligations must be stated, not assumed.** For every new interactive pattern: keyboard navigation order (Tab sequence; do modal dialogs trap focus?); screen reader role and label (`role="dialog"`, `aria-labelledby`, `aria-describedby`); focus management (where does focus go after a modal opens? after a form submits? after a list item is deleted?); color is not the only differentiator for meaning (error states must include icon or text label, not only a red border — WCAG 1.4.1 Use of Color). The brief does not need to specify ARIA implementation details — it must state what the accessibility behavior should be.
- **Reuse expectations must be explicit.** For every component referenced in the brief: "use existing `<DataTable>` component from design system" vs. "this pattern does not exist in the design system — new component required." New component proposals must include the reuse justification (who else will use it?) and trigger a design-system-rules review before implementation.

# Industry Benchmarks

Anchor against: **WCAG 2.2 (Web Content Accessibility Guidelines)** — 1.3.1 Info and Relationships (programmatic structure); 1.4.1 Use of Color (color not sole indicator); 2.1.1 Keyboard (all functionality keyboard accessible); 2.4.3 Focus Order (logical focus sequence); 3.3.1 Error Identification (text description of error); 3.3.2 Labels or Instructions; 3.3.4 Error Prevention. **Nielsen Norman Group (nngroup.com)** — Error Message Guidelines (specific, constructive, polite); Inline Validation timing; Progressive Disclosure; Visibility of System Status (Heuristic #1). **Luke Wroblewski "Web Form Design" (2008)** — top-aligned labels; inline validation timing research; field order by user decision flow; error placement (inline, not top-of-form). **Brad Frost "Atomic Design"** — component taxonomy referenced in brief: atom (input, button), molecule (form group), organism (checkout section); ensures brief language aligns with design system vocabulary. **Apple Human Interface Guidelines / Material Design 3 / Fluent 2** — platform-specific interaction conventions for mobile/desktop; used when the brief targets a specific platform. **ARIA Authoring Practices Guide (APG) (w3.org/WAI/ARIA/apg/)** — dialog pattern, combobox pattern, disclosure pattern; keyboard interaction specifications for complex widgets.

### Interaction State Coverage Matrix

| Surface Type | Required States | Loading Indicator | Empty State | Error State | Success State |
| --- | --- | --- | --- | --- | --- |
| Data list / table | idle, loading, empty, error | Skeleton rows or spinner | "No items yet" + primary action CTA | "Failed to load" + retry action | N/A |
| Form (create/edit) | idle, submitting, field errors, system error, success | Submit button shows spinner | N/A (form is always present) | Inline field errors + optional system banner | Success message or redirect |
| Multi-step wizard | idle per step, submitting final step | Step transition animation | N/A | Per-step validation errors | Confirmation step with summary |
| Action button (destructive) | enabled, disabled, confirming, loading, completed | Button loading state | N/A | Error toast / inline error | Success toast / visual state change |
| Search / filter | idle, loading results, no results, error | Skeleton or spinner below input | "No results for X" + clear filter action | "Search failed" + retry | N/A (results are the success state) |
| Modal / dialog | closed, open, loading, error, confirming | Content area spinner | N/A | Error within modal (do not close on error) | Close + optional confirmation |

### Prototype Brief Template

```
Surface: [Name of the screen, panel, or workflow step]
User Goal: [What the user is trying to accomplish]
Trigger: [How the user arrives here — route, link, button, deep link]

Information Hierarchy (top to bottom, primary to secondary):
  1. [Most important content / primary action]
  2. [Supporting context]
  3. [Secondary / optional content]
  4. [Destructive action — bottom, visually separated]

Primary Action: [Label] → [Result / navigation target]
Secondary Action: [Label] → [Result]
Destructive Action (if any): [Label] → [Confirmation required? → Consequence]

Validation:
  Timing: [on-submit / on-blur / on-change for specific fields]
  Fields: [field name → rule → error message → placement]
  Cross-field: [e.g., "end date must be after start date"]
  Server-side: [async validation → loading state → error placement]
  Input preservation: [user input is never cleared on validation failure]

States:
  Idle: [describe default loaded state]
  Loading: [what is shown during async operations]
  Empty: [empty state copy + available actions]
  Error (field): [inline below field; icon + text label]
  Error (system): [banner or inline; retry action available]
  Disabled: [which actions are disabled and under what conditions]
  Success: [confirmation copy + next action or auto-redirect]

Accessibility:
  Keyboard nav: [Tab order; Enter/Space behavior; Escape for dismissal]
  Focus management: [where does focus go on open / submit / close / delete]
  Screen reader: [role; aria-label or aria-labelledby; live regions for status changes]
  Color independence: [error/success conveyed by icon+text, not only color]

Design System Reuse:
  [Component name] — use existing / extend / new (justify + trigger design-system-rules review)

Open Decisions:
  [List any unresolved questions that need product or design input before implementation]
```

# Selection Rules

Select this capability when implementers need **UI intent precise enough to build a professional experience without a full design file**. Route elsewhere when: **design-system-rules** is primary (which existing components to use, how to extend the design system, variant governance); **interaction-state-modeling** is primary (detailed state machine design for a complex interactive flow — e.g., a multi-step checkout with 12 distinct states and branching logic); **page-component-decomposition** is primary (which React/Vue components own which responsibilities on an already-understood page); **user-flow-modeling** is primary (mapping the complete journey across multiple pages, not specifying the UI behavior of one surface).

# Risk Escalation Rules

Escalate when: the brief introduces a new component pattern not present in the design system (requires design-system-rules review and approved design before implementation); a change affects a critical data entry path (financial transactions, medical data entry, legal documents — accessibility must be explicitly reviewed, not assumed); the interaction requires conveying important information through color alone (accessibility violation — WCAG 1.4.1); a new form collects sensitive user data (PII, financial data) and data handling behavior is not yet defined; or the prototype description conflicts with an existing user flow (e.g., introduces a second path to the same action that contradicts the primary navigation model).

# Critical Details

- **Empty states are as important as the populated state.** A dashboard showing "no data yet" for a new user is the user's first impression of the product. An empty state with no guidance, no call to action, and no explanation of why there is no data is a UX failure. The brief must define: what is shown when the list/table/chart has zero records; whether there is a primary action to create the first record; what copy explains the empty condition.
- **Destructive actions require confirmation and must be visually separated.** "Delete account", "Cancel subscription", "Discard draft" — destructive actions must not be adjacent to primary actions (accidental clicks), must use a confirmation dialog or inline confirmation step, and must state the consequence clearly ("This will permanently delete 47 orders and cannot be undone"). The brief must specify the confirmation mechanism and the consequence copy — not just "confirm before delete."
- **Loading states must be designed, not inferred.** "Show a spinner" is not a loading state design. The brief must specify: what exactly is shown while loading (skeleton UI vs spinner vs blank page); whether partial data can be shown while the rest loads; what happens if loading takes > 5 seconds (timeout message, retry action); whether the page is interactive during loading (can the user navigate away safely?). Loading state omissions are the most common cause of blank screens in production.
- **Prototype briefs are owned by product, reviewed by UX, and implemented by engineering.** A brief written by engineering without product input may optimize for implementation convenience rather than user decision flow. A brief written by product without engineering review may propose interactions that are impossible with the current component system. The brief is a collaboration artifact, not a unilateral specification.

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

- Implementation ships with no empty state on a data list — new users see a blank page with no explanation or next action; perceived as broken.
- Error state for a payment form shows only a red border without text — screen reader users cannot identify which field failed; accessibility audit finding post-launch.
- Form resets on validation failure — user has entered 20 fields; submit fails due to server error; all data is lost; user abandons.
- "Confirm delete" dialog is implemented as a simple window.confirm() — blocks thread, cannot be styled, does not meet accessibility requirements; replaced 3 months later.
- Loading state not defined in brief — engineer renders blank page during API call; 500ms of blank page on every navigation; reported as "the app is broken" by users.
- New component invented without reuse justification — a custom date picker is built that duplicates the design system date picker but has different keyboard behavior; two implementations maintained indefinitely.

# Output Contract

Return a prototype brief with:

- `surface` (name; user goal; trigger / how user arrives)
- `information_hierarchy` (ordered list: most important → least important; justified by user decision order)
- `actions` (primary action: label + result; secondary actions; destructive action: label + confirmation + consequence copy)
- `validation` (per field: rule, error message, placement; timing: on-submit/on-blur/on-change; input preservation guarantee)
- `states` (idle, loading, empty, error: field and system, disabled conditions, success)
- `accessibility` (keyboard nav order; focus management; screen reader role + label; color independence confirmation)
- `design_system_reuse` (per referenced component: existing / extend / new + justification)
- `open_decisions` (unresolved product, design, or technical questions blocking implementation)

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

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `design-system-rules` for component selection and new component governance; `interaction-state-modeling` for detailed state machine design for complex multi-step flows; `page-component-decomposition` for component responsibility mapping; `frontend-testing` for test strategy based on the defined states.

# Completion Criteria

The capability is complete when **UI intent is specific enough that two engineers would produce consistent implementations independently, every interactive state is defined, accessibility obligations are stated, and visual execution is fully delegated to the design system**.
