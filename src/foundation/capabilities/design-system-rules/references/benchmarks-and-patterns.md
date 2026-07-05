# Design System Rules Benchmarks And Patterns

Use this reference when a design-system-rules output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, evidence, output contract, and quality gates.

## Benchmark Anchors

- WCAG 2.2 AA: minimum accessibility baseline for contrast, focus visible, target size, labels, and status messages.
- WAI-ARIA 1.2 and ARIA Authoring Practices Guide: role, state, property, keyboard interaction, and composite-widget semantics.
- APCA: emerging perceptual contrast model to monitor for WCAG 3.0 readiness; do not replace current WCAG AA thresholds unless project policy says so.
- Material Design 3, Apple HIG, Fluent 2, and Spectrum: mature component, token, accessibility, motion, density, and cross-platform governance examples.
- axe-core, Storybook accessibility addon, Lighthouse accessibility scoring, and Playwright accessibility checks: automated signals for common violations.
- ISO 9241-171 and Section 508: accessibility and ergonomics governance for regulated or public-sector surfaces.

## Component Selection Decision Tree

```text
Is there an existing component that serves this interaction?
  YES -> Use existing component and defined variants only.
    Is an edge-case variant needed?
      YES, it maps to a product state -> Add variant through design-system governance.
      YES, it is one-off styling -> Reject; use the closest existing variant.
  NO -> Is the interaction semantics genuinely new?
    NO -> Compose existing primitives.
    YES -> Does it recur on at least 3 surfaces or have explicit design-lead exception?
      NO -> Use feature-local composition; record future revisit signal.
      YES -> New component proposal with interaction spec, accessibility spec, API, tokens, owner, stories, docs, and tests.
```

## Variant Axis Governance

| Axis | Sanctioned values | Review focus |
| --- | --- | --- |
| `intent` | `primary`, `secondary`, `danger`, `warning`, `success`, `info`, `neutral` | Maps to user decision weight and semantic consequence. |
| `size` | `xs`, `sm`, `md`, `lg`, `xl` | Follows spacing and typography scale; no raw px exceptions. |
| `density` | `default`, `compact` | Chosen by task density and viewport, not visual preference. |
| `state` | `default`, `hover`, `active`, `focus`, `disabled`, `loading`, `error`, `selected` | Every state has accessible styling and test evidence. |
| `theme` | `light`, `dark`, approved brand theme | Text and UI contrast pass in each theme. |
| `motion` | `none`, `subtle`, `transition`, `emphasis` | Purposeful and respects `prefers-reduced-motion`. |
| Custom | Forbidden by default | Requires governance approval, owner, docs, and migration/deprecation rule. |

## WCAG 2.2 AA Quick Checklist

| Criterion | Requirement | Evidence |
| --- | --- | --- |
| 1.1.1 Non-text Content | Images have useful `alt`; decorative images use empty alt. | axe plus manual review for meaning. |
| 1.3.1 Info and Relationships | Structure communicated by semantics, not only visual layout. | DOM role/heading/label inspection. |
| 1.4.1 Use of Color | Error, status, and selection are not color-only. | State screenshot or story. |
| 1.4.3 Contrast Minimum | Text contrast at least 4.5:1, or 3:1 for large text. | Contrast result for each theme. |
| 1.4.11 Non-text Contrast | UI components and graphics at least 3:1. | Contrast result for controls, borders, icons. |
| 2.1.1 Keyboard | All functionality available by keyboard. | Keyboard sequence or Playwright proof. |
| 2.4.3 Focus Order | Focus order preserves meaning and operability. | Tab path review. |
| 2.4.7 Focus Visible | Keyboard focus indicator always visible. | Screenshot or manual check. |
| 2.5.3 Label in Name | Visible label text appears in accessible name. | Accessibility tree or Testing Library query. |
| 2.5.8 Target Size Minimum | Interactive targets at least 24 by 24 CSS px. | Manual/device check. |
| 3.3.1 Error Identification | Errors are described in text, not color alone. | Error state story/test. |
| 3.3.2 Labels or Instructions | Inputs have labels and required/format guidance. | axe plus manual review. |
| 4.1.2 Name, Role, Value | Custom controls expose programmatic name, role, and state. | axe/manual APG review. |
| 4.1.3 Status Messages | Async status updates are announced without moving focus. | live-region test or manual screen-reader note. |

## Responsive Behavior Checklist

| Context | Check | Minimum standard |
| --- | --- | --- |
| Mobile 320-767px | Primary action reachable and not hidden by overflow. | Above fold where practical or sticky/in-flow action after required fields. |
| Mobile touch | Targets have adequate hit area and spacing. | At least 24 by 24 CSS px; 44 by 44 preferred for high-frequency actions. |
| Mobile text | Labels, values, and actions wrap or truncate predictably. | No horizontal page scroll at 320px; truncation preserves meaning. |
| Tablet 768-1023px | Two-pane or side-nav layouts collapse gracefully. | Navigation and content remain keyboard and touch operable. |
| Desktop 1024-1439px | Dense layouts preserve scan order and action hierarchy. | No unrelated cards-in-cards or over-fragmented sections. |
| Wide 1440px+ | Reading line length and empty space remain controlled. | Text regions generally stay below 80ch unless data layout requires more. |
| Data tables | Overflow or summarization strategy is explicit. | Horizontal scroll, priority columns, stacked rows, or summary/detail split. |
| Forms | Field groups and validation messages remain associated. | Labels/errors stay near controls and are announced programmatically. |

## New Component Proposal Evidence Pack

Require all of the following before approving a new design-system component:

- Interaction semantics differ from existing primitives or composition.
- At least 3 current product surfaces need the component, or a design lead approves an exception with review date.
- API is small, product-state-driven, and free of screen-specific vocabulary.
- Variant axes and invalid prop combinations are documented.
- Accessibility spec names roles, keyboard behavior, focus behavior, live regions, contrast, and target size.
- Token usage is complete: no raw colors, spacing, typography, radius, shadow, or motion values.
- Responsive behavior is defined for mobile, tablet, desktop, and wide contexts.
- Storybook stories cover every state, theme, density, and important variant.
- Tests cover keyboard path, disabled/loading/error states, and axe or equivalent accessibility scan.
- Owner, documentation location, migration path, and deprecation policy are named.

## Review Questions

1. Which current components, stories, or tokens were inspected?
2. Which closest alternatives were rejected and why?
3. Is the decision about component semantics, visual preference, layout ownership, state behavior, or test coverage?
4. Which variants map to real product states?
5. Which variant combinations are invalid or unsupported?
6. Which WCAG criteria are in scope for each interactive element?
7. Which keyboard path and focus movement prove the component is operable?
8. Which breakpoint can hide or reorder the primary action?
9. Which text, number, locale, or translation length can overflow?
10. Which evidence is automated, and which needs manual/specialist review?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Raw hex, px, or font family in component code | Breaks themes, brand updates, and contrast governance. | Use exported tokens and record token source. |
| New shared component for one dashboard | No reuse pressure; future API will grow speculative flags. | Keep feature-local or compose existing primitives. |
| Variant prop named for a screen, such as `salesDashboardCompact` | Encodes page context instead of product state. | Use density/state/intent axis or reject the variant. |
| Accessibility note says only "run axe" | Automated checks miss keyboard flow, meaning, and screen-reader behavior. | Map WCAG criteria and manual checks per state. |
| Desktop-only responsive proof | Mobile task completion may be impossible. | Define breakpoint behavior and run viewport checks. |
| Color-only status or error state | Violates use-of-color and excludes color-blind users. | Add text/icon/ARIA state and test it. |
| Animation without reduced-motion behavior | Can trigger vestibular issues and violates user preference. | Respect `prefers-reduced-motion` and explain animation purpose. |
