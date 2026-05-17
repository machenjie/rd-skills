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

# Non-Negotiable Rules

- **Reuse existing components and variants first.** A new component is only justified when: (1) the interaction semantics genuinely differ from all existing components; (2) the need will recur in at least 3 distinct product surfaces; (3) a reuse owner and documentation plan are identified. Custom one-off styling is not a justification for a new primitive.
- **Accessibility is non-negotiable from first implementation.** WCAG 2.2 Level AA is the minimum. Criteria that cannot be retrofitted: 1.4.11 Non-text Contrast (≥ 3:1 for UI components), 1.4.3 Text Contrast (≥ 4.5:1), 2.4.7 Focus Visible, 2.5.8 Target Size Minimum (24×24 CSS px), 4.1.2 Name/Role/Value (ARIA semantics). Never defer accessibility to a separate "accessibility pass."
- **Variants encode product states, not visual preferences.** Allowed variant axes: `intent` (primary/secondary/danger/warning/success/info), `size` (sm/md/lg), `density` (default/compact), `state` (default/hover/active/disabled/loading/error). Forbidden: ad hoc color overrides, unsanctioned font-size props, inline style overrides to satisfy one screen's design.
- **Design tokens are the only sanctioned styling mechanism.** Direct hex codes, hardcoded px values, and font family strings in component code are violations. Use only design-system–exported tokens: `color.*`, `space.*`, `typography.*`, `radius.*`, `shadow.*`, `motion.*`.
- **Responsive rules cover the full task, not just the viewport.** For each responsive state (mobile, tablet, desktop, wide): primary action must be reachable, text must not overflow or become unreadable, touch targets must meet 44×44 CSS px (WCAG 2.5.5 AAA) or 24×24 minimum (2.5.8 AA), form fields must remain operable, data tables must have a defined overflow strategy (scroll, collapse, or summarize).
- **Focus management is explicit for dynamic content.** When a modal, drawer, toast, or popover opens, focus must move to the first focusable element or the container. When it closes, focus must return to the trigger. Dialogs must trap focus. `aria-live` regions must be declared for async state updates.
- **Component API stability is a compatibility contract.** Once a component is released to the design system, removing a prop or changing its semantics is a breaking change. Additions are non-breaking. Deprecation requires a migration path and a minimum 2-sprint notice.

# Industry Benchmarks

Anchor against: **WCAG 2.2** (W3C/ISO 40500:2012) — web accessibility standard; AA is the legal minimum in most jurisdictions (EU EHRC, US ADA, UK Equality Act). **WAI-ARIA 1.2** — semantic role, state, and property specification for interactive components. **APCA (Accessible Perceptual Contrast Algorithm)** — emerging replacement for WCAG contrast ratio; monitor for WCAG 3.0 adoption. **Material Design 3** (Google) — production design-system with documented component specs, variant axes, and motion guidelines. **Apple HIG** — Human Interface Guidelines; canonical reference for iOS/macOS native component semantics and accessibility. **Fluent 2** (Microsoft) — enterprise component governance model with token architecture. **Spectrum** (Adobe) — cross-platform design system with accessibility-first component specs. **ARIA Authoring Practices Guide (APG)** — W3C patterns for keyboard interaction and ARIA usage per component type. **axe-core** / **Deque Axe** — automated accessibility testing; 57% of WCAG failures are automatable. **Storybook Accessibility Addon** — accessibility auditing integrated into component development. **Lighthouse Accessibility Score** ≥ 90 — project-level target. **ISO 9241-171:2008** — ergonomics of software for accessibility. **Section 508** (US federal) — requires WCAG 2.0 AA compliance for US federal-facing software.

### Component Selection Decision Tree

```
Is there an existing component that serves this interaction?
├── YES → Use existing component + defined variants only
│   └── Is an edge case variant needed?
│       ├── YES, it maps to a product state → Add variant through design-system governance
│       └── YES, it's one-off styling → Reject; use closest existing variant
└── NO → Is the interaction semantics genuinely new?
    ├── NO → Decompose into composition of existing primitives
    └── YES → Does it recur on ≥ 3 surfaces?
        ├── NO → Use composition; escalate for future new-component proposal
        └── YES → New component: requires interaction spec, accessibility spec,
                  API design, token usage, Storybook story, owner, and review
```

### Variant Axis Governance

| Axis | Sanctioned values | Notes |
| --- | --- | --- |
| `intent` | `primary`, `secondary`, `danger`, `warning`, `success`, `info`, `neutral` | Maps to user decision weight |
| `size` | `xs`, `sm`, `md`, `lg`, `xl` | Must match spacing-scale increments |
| `density` | `default`, `compact` | Data-dense UI vs. consumer UI |
| `state` | `default`, `hover`, `active`, `focus`, `disabled`, `loading`, `error`, `selected` | All states must have accessible styling |
| `theme` | `light`, `dark` | Must pass contrast requirements in both |
| Custom | ❌ Forbidden | Ad hoc size overrides, color overrides, font overrides |

### WCAG 2.2 AA Quick Checklist

| Criterion | Requirement | Auto-testable? |
| --- | --- | --- |
| 1.1.1 Non-text content | All images have `alt`; decorative images use `alt=""` | Yes (axe) |
| 1.3.1 Info and Relationships | Structure communicated via semantics, not only visually | Partial |
| 1.4.3 Contrast (Minimum) | Text ≥ 4.5:1 (normal), ≥ 3:1 (large text ≥ 18pt/14pt bold) | Yes |
| 1.4.11 Non-text Contrast | UI components and graphics ≥ 3:1 | Yes |
| 2.4.7 Focus Visible | Keyboard focus indicator always visible | Yes |
| 2.5.3 Label in Name | Visible label text is part of accessible name | Partial |
| 2.5.8 Target Size (Minimum) | Interactive targets ≥ 24×24 CSS px | Manual |
| 3.3.1 Error Identification | Errors described in text; not only color | Partial |
| 3.3.2 Labels or Instructions | Form fields have labels; required clearly indicated | Yes |
| 4.1.2 Name/Role/Value | All UI components have programmatic name and role | Yes (axe) |
| 4.1.3 Status Messages | Live regions for async status updates | Manual |

### Responsive Behavior Checklist

| Viewport | Check | Minimum standard |
| --- | --- | --- |
| Mobile (320–767px) | Primary action reachable without scroll? | Yes, above fold or in sticky CTA |
| Mobile | Touch targets ≥ 44×44 CSS px? | WCAG 2.5.5 AAA (recommended) |
| Mobile | Text does not overflow container | No horizontal scroll at 320px |
| Tablet (768–1023px) | Two-pane layouts collapse gracefully? | Side nav collapses to hamburger or bottom nav |
| All | Form fields operable without horizontal scroll | 100% viewport width forms acceptable |
| All | Data tables have overflow strategy | Horizontal scroll, priority column hide, or card layout |
| Wide (1440px+) | Max-width container to prevent line length > 80ch? | Reading legibility maintained |

# Selection Rules

Select this capability when **component choice, variant governance, accessibility requirements, or responsive behavior** are primary design decisions. Adjacent routing:

- Prefer `prototype-description` when the UI interaction intent is not yet decided.
- Prefer `information-architecture` when navigation structure and content hierarchy are primary.
- Prefer `routing-navigation-design` when URL routing and screen transitions are primary.
- Prefer `form-validation-design` when form input validation semantics are the focus.
- Prefer `frontend-change-builder` for implementation execution after design decisions are made.
- Prefer `frontend-testing` when visual regression, accessibility, and cross-browser coverage are the focus.

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

- `components_to_use` (exact names from design system; links to Storybook stories)
- `variants_required` (axis + value pairs; justification if non-standard)
- `variants_forbidden` (list of disallowed prop combinations for this use case)
- `accessibility_requirements` (WCAG criteria per SC number; ARIA roles/properties; keyboard navigation pattern; focus management spec)
- `responsive_behavior` (per breakpoint: layout strategy, action visibility, overflow handling)
- `tokens_used` (list of design tokens; confirm no raw hex/px values)
- `motion_behavior` (`prefers-reduced-motion` compliance; animation purpose)
- `new_component_justification` (if applicable: reuse need, interaction difference, API design, owner)
- `test_requirements` (axe-core, Lighthouse, keyboard navigation, screen reader, cross-browser)
- `review_evidence` (screenshots of all states; contrast check results; WCAG checklist completion)

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

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `frontend-change-builder` for implementation; `frontend-testing` for visual regression, Lighthouse, and cross-browser coverage; `prototype-description` when interaction intent needs further definition; specialist accessibility review when ARIA patterns involve complex composite widgets (data grid, combobox, tree).

# Completion Criteria

The capability is complete when every UI component choice, variant, token, accessibility requirement, and responsive behavior is **governed by design-system rules** — with no hardcoded values, no unjustified new primitives, no unresolved WCAG violations, and all interactive states designed before implementation begins.
