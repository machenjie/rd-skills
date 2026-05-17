---
name: page-component-decomposition
description: Defines page component responsibilities, state ownership, boundaries, and decomposition depth without creating giant components or premature micro-components.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "31"
changeforge_version: 0.1.0
---

# Mission

**Decompose frontend pages into components with clear responsibilities, explicit state ownership, testable side-effect boundaries, and maintainable depth** — preventing both giant mixed-responsibility components that are impossible to test in isolation and premature micro-component fragmentation that buries simple logic behind unnecessary abstraction layers.

# When To Use

Use this capability when a change: adds a new page, screen, or multi-step workflow surface; introduces a shared component intended for reuse across multiple features; reshapes an existing component that has grown beyond a single responsibility; changes props contracts, state ownership, or data-fetching responsibility of existing components; or is flagged in review for "this component does too much", "why is data being fetched here?", or "we're drilling props through 5 layers."

# Do Not Use When

Do not use this capability to: split a stable, small, single-responsibility component for aesthetic preference without a behavioral or testability justification; create reusable abstractions before they are needed by at least two distinct consumers with stable requirements (YAGNI); document framework-specific component lifecycle mechanics (use framework documentation); or reorganize components solely to match a folder naming convention without an ownership or testability benefit.

# Non-Negotiable Rules

- **Each component must have exactly one responsibility.** A component is correctly scoped if you can state its responsibility in one sentence without "and". "Displays user profile" — correct. "Loads user data, validates the form, renders the profile, and handles subscription upgrade" — four responsibilities; split into Page + FeatureSection + Form + Primitive. The litmus test: can this component be replaced without changing any sibling component?
- **State must be owned at the nearest component that can update, validate, and reset it correctly.** Lifting state too high creates unnecessary re-renders and unclear reset behavior. Keeping state too low creates prop drilling or sibling communication impossible. Rule: start with local state; lift to nearest common ancestor only when sibling coordination, form submission, or persistence requires a single owner.
- **Presentational components must not perform side effects.** A presentational component (renders UI from props, emits events via callbacks) must not: fetch data, navigate programmatically, check permissions, mutate global state, or interact with external APIs. Side effects belong in container components, custom hooks, or page-level orchestrators. The test: a presentational component must be fully renderable with only its props — no mock store, no network, no router.
- **Permission and authorization checks must not be buried inside presentational components.** `if (!user.canEdit) return null` inside a `<Button>` component — the authorization decision is invisible to the parent orchestrating the page. Permission checks belong at the page or feature-section level, where they are visible and testable. Presentational components receive already-computed `disabled` or `visible` props.
- **Data fetching must happen at the nearest container that needs the data.** Do not fetch in `App` root and drill through 8 layers. Do not fetch the same data independently in three sibling components. Use co-location: fetch at the page or feature-section level; pass data down as props or use context scoped to the feature. TanStack Query / SWR / RTK Query — co-locate the query hook with the component that owns the data requirement.
- **Reuse requires two stable consumers, not one anticipated consumer.** A `<UserCard>` used in exactly one place is not a shared component — it is a feature component that happens to be named generically. Extract to a shared component only when there are ≥ 2 consumers with overlapping requirements. Premature generalization adds complexity without benefit and creates a maintenance burden when the two anticipated use cases differ.
- **Component depth must not exceed the cognitive load threshold.** When a page component renders feature sections, each section renders form groups, each form group renders field sets, each field set renders individual fields — the hierarchy is 5 levels deep. If reading a bug report requires traversing more than 4 levels to find the relevant component, the decomposition has added complexity rather than reducing it. Prefer flat hierarchies with co-location over deep hierarchies.

# Industry Benchmarks

Anchor against: **Dan Abramov "Presentational and Container Components"** (medium.com/@dan_abramov, 2015; later reconsidered — hooks changed the model) — core insight still valid: separate "how things look" from "how things work," but use hooks instead of class-based containers. **React docs "Thinking in React"** — component hierarchy design; single responsibility; state co-location; prop drilling vs context. **Kent C. Dodds "Application State Management with React"** — co-location principle: "The best place to put state is as close to where it's used as possible." **Brad Frost "Atomic Design"** — atoms (primitives), molecules (simple groups), organisms (feature sections), templates (page layouts), pages (instances); useful taxonomy for design system boundaries. **TanStack Query (React Query) co-location pattern** — query hook at the component that owns the data requirement; avoids prop drilling of data while keeping fetch logic co-located. **Storybook component-driven development** — each component should be independently renderable in Storybook with props only; no global providers or stores required for isolation. **Testing Library "Testing Philosophy"** (testing-library.com) — test user behavior, not implementation; components that are too large cannot be tested at the right granularity; components that are too small produce tests that test implementation details. **WCAG 2.1 §1.3 Adaptable** — component structure must convey meaning independently of presentation; state changes (loading, error, empty, disabled) must be communicated via accessible roles and attributes.

### Component Responsibility Classification

| Component Type | Owns | Must Not Contain | State Ownership | Test Focus |
| --- | --- | --- | --- | --- |
| Page Orchestrator | Route context, URL params, permission gate, data-fetch coordination, layout | Business logic, domain calculations | Global / URL state | Route guard, permission rendering, data loading state |
| Feature Section | Single feature workflow (form, list, wizard step) | Cross-feature coordination | Local feature state, lifted on sibling need | Feature behavior, submission, error states |
| Shared UI Primitive | Single UI interaction (button, input, modal, badge) | Data fetching, business logic, navigation | No state or minimal local (e.g., open/closed) | Props → render output, ARIA attributes, callbacks |
| Container / Hook | Data fetching, cache management, side-effect orchestration | UI rendering | Derived from server/global state | Loading/error/success states, cache invalidation |
| Layout | Structural composition (header, sidebar, grid) | Data dependencies, business logic | None | Responsive rendering, slot composition |

### State Ownership Decision Tree

```
Does only ONE component need to read and update this state?
  YES → Keep local state (useState / useReducer)

Do SIBLING components need to read the same state?
  YES → Lift to nearest common parent (prop drilling if shallow)
  YES + deep tree → Use context scoped to feature boundary (FeatureContext)

Does the state need to persist across route changes or be shared globally?
  YES → Global state manager (Zustand, Redux, Jotai) OR URL state (searchParams)

Is the state server-derived (fetched from API)?
  YES → TanStack Query / SWR / RTK Query; co-locate with the component that needs it
  YES + multiple components need same data → deduplicate via query key; cache is shared

Is the state URL-addressable (shareable links, back-button behavior)?
  YES → URL state (useSearchParams, path params); never in component local state

Anti-pattern signals:
  ⚠ State in App root, passed as props 8 levels down → move to feature context or query cache
  ⚠ Same API called 3 times for same data → share query key; TanStack Query deduplicates
  ⚠ State reset requires unmounting a parent → state is too high; move down to owner component
```

### Component Decomposition Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| `OrderPage.tsx` is 800 lines: fetches data, validates form, renders table, handles payments | Untestable as a unit; any change risks regression across all 4 responsibilities | Split: `OrderPage` (orchestrator) → `OrderList` (display) + `OrderForm` (submission) + `PaymentSection` (payment handling) |
| `<Button disabled={!user.roles.includes('admin')}>` | Authorization logic inside presentational primitive; invisible to parent; duplicated across buttons | Compute `canPerformAction` at page/feature level; pass `disabled={!canPerformAction}` |
| `<UserCard>` fetches user data internally | Cannot render in Storybook without API; cannot test without mock server; breaks component isolation | Move fetch to parent container or custom hook; `<UserCard>` receives `user: User` prop |
| `<StatusBadge>` has 12 props for every possible customization | Props explosion for a simple display component | Accept a `variant` enum + `label` string; design system governs visual variants |
| Prop drilling: `App → Page → Section → Row → Cell → Icon` — passing `theme` 6 levels | Component hierarchy couples all parents to child's theme need | Use React Context for cross-cutting concerns (theme, locale); do not prop-drill stable values |
| `<SearchPage>` extracted as shared component used in one place | Premature reuse; next consumer has different requirements; component gets feature flags and conditional logic | Keep as feature component until second stable consumer exists |

# Selection Rules

Select this capability when the main decision is **how a page or screen should be decomposed into components with correct responsibility and state ownership**. Route elsewhere when: **state-management-design** is primary (choosing between Redux, Zustand, Context API, URL state — source-of-truth architecture decisions); **routing-navigation-design** is primary (URL structure, guards, lazy loading of routes); **design-system-rules** is primary (shared component governance, design tokens, visual standards); **frontend-testing** is primary (test strategy and coverage for already-decomposed components). This capability governs the decomposition decision; those capabilities govern implementation details within the decomposed structure.

# Risk Escalation Rules

Escalate when: a single component owns multiple user-visible workflows (form submission + data loading + table rendering + permission checks); a component performs data fetching and contains business logic that should be isolated for testing; a shared component is proposed for extraction but has only one consumer with unstable requirements; prop drilling exceeds 4 levels across unrelated components; or a frontend performance issue is traced to N+1 component-level fetching (each component in a list fetches its own data independently). Escalate to experience-impact-modeler when component structure changes affect the user journey task model.

# Critical Details

- **The "too large" signal is testability, not line count.** A 400-line component that handles one clearly bounded workflow (multi-step wizard with complex state) may be appropriately sized. An 80-line component that mixes fetching, validation, rendering, and navigation is too large by responsibility — not by lines. The test: can you write an isolated unit test for the component's behavior without mocking 6 other things?
- **Custom hooks are the correct abstraction for shared behavior, not shared components.** If two components share data fetching logic for the same resource, extract a custom hook (`useOrderData()`) — not a wrapper component. Custom hooks compose behavior; components compose UI.
- **Context is not a substitute for correct state location.** Context solves "I need to avoid drilling props through unrelated intermediaries." It does not solve "I don't know who should own this state." Before reaching for context, confirm state ownership. Context scoped to a feature boundary (not global app context) is acceptable for feature-internal coordination.
- **Storybook-first decomposition prevents untestable components.** When designing a new component, ask: "Can I write a Storybook story for this component's every meaningful state with props only?" If the answer is no (requires mock store, active router, or network call), the component has too many responsibilities or owns state it should not own.

# Failure Modes

- `OrderManagementPage.tsx` reaches 1,200 lines over 6 months — every bug fix requires reading the entire file; test coverage drops to 12% because engineers cannot write isolated tests for individual behaviors.
- Presentational `<ProductCard>` component fetches its own reviews — 24 ProductCard components on a search results page make 24 separate API calls; N+1 rendering problem; page response time dominated by component-level fetches.
- Permission check inside `<ActionMenu>` — backend role change removes `admin` permission; frontend still renders the menu because the check is reading from stale local state rather than being enforced at the page level with fresh data.
- State lifted to `App` root to share between two pages — every component in the tree re-renders on state change; list of 500 items re-renders on a filter input keystroke; performance degrades.
- Shared `<DataTable>` component extracted before requirements are stable — two consumers diverge; component accumulates 40 props and conditional branches; neither consumer is well served; rewrite required.
- Component depth of 7 levels — a bug report says "the delete button doesn't work"; engineer must open 7 files to find which component handles the delete action; 45-minute investigation for a 3-line fix.

# Output Contract

Return a component decomposition map with:

- `page_owner` (component name; responsibility; route context; permission gate location; data-fetch orchestration)
- `component_tree` (hierarchy: page → feature sections → shared primitives; depth ≤ 4 for most features)
- `component_responsibilities` (per component: one-sentence responsibility; owned state; data inputs as props; emitted callbacks; side effects)
- `state_ownership` (per state value: owner component; lifting justification if above local; global/URL state rationale)
- `data_fetching_locations` (which component triggers each fetch; query key for cache deduplication; loading/error/empty state handling)
- `permission_check_locations` (which components evaluate permissions; must be page/feature level — not in presentational primitives)
- `shared_component_criteria` (components proposed for reuse: minimum 2 confirmed consumers; stable props contract; design-system alignment)
- `accessibility_states` (per interactive component: idle/loading/disabled/error/success states with ARIA attributes)
- `test_boundaries` (per component: test isolation requirement; Storybook story feasibility; mock requirements)
- `boundaries_not_to_cross` (e.g., no data fetching in primitives; no navigation in form fields; no auth checks in display components)

# Quality Gate

The decomposition is complete only when:

1. Every component has a single-sentence responsibility without "and."
2. No presentational component fetches data, navigates, or checks permissions.
3. State is owned at the nearest component that can update, validate, and reset it correctly.
4. Permission and authorization checks are at page or feature-section level — visible and testable.
5. Data fetching is co-located at the component level that owns the data requirement; no redundant sibling fetches for the same resource.
6. Shared components have ≥ 2 confirmed stable consumers before extraction.
7. Component hierarchy depth ≤ 4 for most features (justified exception documented if deeper).
8. Every component is independently renderable in Storybook or test with props only (no global provider required).
9. All interactive states (loading, error, empty, disabled, permission-denied) modeled and mapped to ARIA attributes.
10. No prop drilling beyond 3 levels for stable cross-cutting values (use context for deeper needs).

# Used By

- frontend-change-builder
- experience-impact-modeler

# Handoff

Hand off to `state-management-design` for global state source decisions and state architecture; `interaction-state-modeling` for UI state machine design (loading/error/empty/disabled coverage); `design-system-rules` for shared component governance and design token contracts; `frontend-testing` for component test strategy and Storybook coverage.

# Completion Criteria

The capability is complete when **every component has a single explicit responsibility, state ownership is defined at the nearest correct owner, presentational components are free of side effects and authorization logic, data fetching is co-located with data consumers, and every component is independently testable without global providers or network mocks**.
