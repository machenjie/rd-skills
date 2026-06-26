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

# Stage Fit

Use during frontend planning when a page, screen, route, or workflow needs an implementable component map; during implementation when ownership of data fetching, state, permissions, callbacks, side effects, or shared primitives is unclear; during review when a component is too large, too fragmented, too coupled to providers, or too speculative for reuse; and during repair when bugs trace to buried state, hidden permission checks, duplicated fetches, or untestable component boundaries. Hand off when the primary decision is navigation structure, complete interaction states, global state architecture, design-system governance, or test execution.

# Non-Negotiable Rules

- **Each component must have exactly one responsibility.** A component is correctly scoped if you can state its responsibility in one sentence without "and". "Displays user profile" — correct. "Loads user data, validates the form, renders the profile, and handles subscription upgrade" — four responsibilities; split into Page + FeatureSection + Form + Primitive. The litmus test: can this component be replaced without changing any sibling component?
- **State must be owned at the nearest component that can update, validate, and reset it correctly.** Lifting state too high creates unnecessary re-renders and unclear reset behavior. Keeping state too low creates prop drilling or sibling communication impossible. Rule: start with local state; lift to nearest common ancestor only when sibling coordination, form submission, or persistence requires a single owner.
- **Presentational components must not perform side effects.** A presentational component (renders UI from props, emits events via callbacks) must not: fetch data, navigate programmatically, check permissions, mutate global state, or interact with external APIs. Side effects belong in container components, custom hooks, or page-level orchestrators. The test: a presentational component must be fully renderable with only its props — no mock store, no network, no router.
- **Permission and authorization checks must not be buried inside presentational components.** `if (!user.canEdit) return null` inside a `<Button>` component — the authorization decision is invisible to the parent orchestrating the page. Permission checks belong at the page or feature-section level, where they are visible and testable. Presentational components receive already-computed `disabled` or `visible` props.
- **Data fetching must happen at the nearest container that needs the data.** Do not fetch in `App` root and drill through 8 layers. Do not fetch the same data independently in three sibling components. Use co-location: fetch at the page or feature-section level; pass data down as props or use context scoped to the feature. TanStack Query / SWR / RTK Query — co-locate the query hook with the component that owns the data requirement.
- **Reuse requires two stable consumers, not one anticipated consumer.** A `<UserCard>` used in exactly one place is not a shared component — it is a feature component that happens to be named generically. Extract to a shared component only when there are ≥ 2 consumers with overlapping requirements. Premature generalization adds complexity without benefit and creates a maintenance burden when the two anticipated use cases differ.
- **Component depth must not exceed the cognitive load threshold.** When a page component renders feature sections, each section renders form groups, each form group renders field sets, each field set renders individual fields — the hierarchy is 5 levels deep. If reading a bug report requires traversing more than 4 levels to find the relevant component, the decomposition has added complexity rather than reducing it. Prefer flat hierarchies with co-location over deep hierarchies.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| New page or screen | New route, screen, tab, workflow page, admin surface, or multi-section feature. | Define page owner, feature sections, primitives, layout slots, state owner, and side-effect owner before implementation. | Route/screen path, user task, data sources, permission gates, component tree depth, ownership map. | `information-architecture`, `interaction-state-modeling`, `frontend-testing` | Splitting by visual boxes only. |
| Giant component decomposition | Component mixes fetching, validation, rendering, mutation, navigation, permission checks, and layout. | Split orchestration, feature behavior, presentational rendering, and side effects without changing visible behavior. | Current responsibilities, extracted owners, old behavior preserved, tests/stories affected, rollback path. | `code-clarity-maintainability`, `frontend-testing`, `refactoring` | Line-count-only split. |
| Shared component proposal | Component is being moved to shared/common/design-system area or given generic API/variants. | Prove stable reuse pressure and prevent shared component pollution. | Confirmed consumers, stable props contract, owner, design-system alignment, rejected feature-local placement. | `design-system-rules`, `implementation-structure-design` | One anticipated future consumer. |
| State and side-effect ownership | Prop drilling, duplicate fetches, context/store proposal, hook extraction, or unclear reset behavior. | Put state/fetch/effects at the nearest correct owner and expose presentational components through props/callbacks. | State inventory, readers/writers, query/cache owner, side-effect location, reset/invalidation behavior. | `state-management-design`, `frontend-api-integration` | Global store as first answer. |
| Permission-sensitive decomposition | Role, tenant, ownership, feature flag, or disabled/hidden actions affect component boundaries. | Keep authorization decisions visible at page/feature level and primitives permission-agnostic. | Permission source, allowed/denied branches, non-leak rule, disabled/hidden treatment, test fixture map. | `permission-boundary-modeling`, `frontend-testing`, `security-privacy-gate` when sensitive | Permission checks inside primitives. |
| Testability and Storybook boundary | Component cannot render without provider/router/network, tests mock internals, or stories are impossible. | Make behavior independently renderable at the right boundary. | Story/test boundary, required providers, mock contract, accessible states, public behavior assertions. | `frontend-testing`, `testability-seam-design` | Exporting private helpers only for tests. |

# Industry Benchmarks

Anchor against React "Thinking in React", presentational/container separation adapted for hooks, state co-location guidance, Atomic Design taxonomy, TanStack Query/SWR query co-location, Storybook component-driven development, Testing Library behavior-first testing, WCAG adaptable/name-role-value requirements, and design-system component governance. Keep this body focused on selection and evidence rules; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for component responsibility matrices, state ownership decision trees, decomposition anti-patterns, and detailed benchmark anchors.

# Selection Rules

Select this capability when the main decision is **how a page or screen should be decomposed into components with correct responsibility and state ownership**. Route elsewhere when: **state-management-design** is primary (choosing between Redux, Zustand, Context API, URL state — source-of-truth architecture decisions); **routing-navigation-design** is primary (URL structure, guards, lazy loading of routes); **design-system-rules** is primary (shared component governance, design tokens, visual standards); **frontend-testing** is primary (test strategy and coverage for already-decomposed components). This capability governs the decomposition decision; those capabilities govern implementation details within the decomposed structure.

# Risk Escalation Rules

Escalate when: a single component owns multiple user-visible workflows (form submission + data loading + table rendering + permission checks); a component performs data fetching and contains business logic that should be isolated for testing; a shared component is proposed for extraction but has only one consumer with unstable requirements; prop drilling exceeds 4 levels across unrelated components; or a frontend performance issue is traced to N+1 component-level fetching (each component in a list fetches its own data independently). Escalate to experience-impact-modeler when component structure changes affect the user journey task model.

# Proactive Professional Triggers

- **Signal:** A page or component diff adds a new hook, context, provider, shared component, or wrapper without a component tree map. **Hidden risk:** ownership shifts are reviewed only as code shape, not as user-visible decomposition. **Required professional action:** produce the decomposition map before accepting the structure. **Route to:** `page-component-decomposition`, `implementation-structure-design`. **Evidence required:** component tree, owner, state/source, side effects, and rejected placements.
- **Signal:** Repository graph or project memory points to a previous component pattern, shared primitive, or provider setup. **Hidden risk:** stale or locally-specialized pattern is copied into the wrong page. **Required professional action:** confirm the current source, consumers, stories, tests, and design-system contract before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`. **Evidence required:** inspected paths, active consumers, accepted/rejected pattern, and freshness limit.
- **Signal:** A presentational component receives permissions, router objects, query clients, stores, or environment-derived data. **Hidden risk:** UI primitives become untestable and hide security or navigation decisions. **Required professional action:** move decisions to page/feature owner and pass computed props/callbacks down. **Route to:** `permission-boundary-modeling`, `state-management-design`, `frontend-testing`. **Evidence required:** before/after owner, primitive props, denied/disabled state, and test boundary.
- **Signal:** A component is split only because it is long, or kept only because it is short. **Hidden risk:** line count replaces responsibility, state ownership, and testability evidence. **Required professional action:** classify responsibilities and prove whether a split or no-split preserves clarity. **Route to:** `code-clarity-maintainability`, `minimal-correct-implementation`. **Evidence required:** one-sentence responsibility, side effects, test seam, depth, and residual complexity.
- **Signal:** A shared component extraction is justified by "we may reuse it later". **Hidden risk:** shared API grows feature flags and variant props before stable reuse exists. **Required professional action:** keep feature-local until reuse pressure is real or document design-system governance. **Route to:** `design-system-rules`, `implementation-structure-design`. **Evidence required:** confirmed consumers, stable contract, owner, and rejected future-proofing.

# Critical Details

- **The "too large" signal is testability, not line count.** A 400-line component that handles one clearly bounded workflow (multi-step wizard with complex state) may be appropriately sized. An 80-line component that mixes fetching, validation, rendering, and navigation is too large by responsibility — not by lines. The test: can you write an isolated unit test for the component's behavior without mocking 6 other things?
- **Custom hooks are the correct abstraction for shared behavior, not shared components.** If two components share data fetching logic for the same resource, extract a custom hook (`useOrderData()`) — not a wrapper component. Custom hooks compose behavior; components compose UI.
- **Context is not a substitute for correct state location.** Context solves "I need to avoid drilling props through unrelated intermediaries." It does not solve "I don't know who should own this state." Before reaching for context, confirm state ownership. Context scoped to a feature boundary (not global app context) is acceptable for feature-internal coordination.
- **Storybook-first decomposition prevents untestable components.** When designing a new component, ask: "Can I write a Storybook story for this component's every meaningful state with props only?" If the answer is no (requires mock store, active router, or network call), the component has too many responsibilities or owns state it should not own.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 component decomposition selection and evidence rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete page/component map, when ownership of state/effects/permissions is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when responsibility classification, state ownership, anti-pattern correction, or benchmark detail is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load these references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Failure Modes

- **Giant orchestrator:** `OrderManagementPage.tsx` reaches 1,200 lines over 6 months; every bug fix requires reading the entire file, and test coverage drops because engineers cannot isolate individual behaviors.
- **Component-level N+1 fetch:** presentational `<ProductCard>` fetches its own reviews; 24 search-result cards make 24 separate API calls and page response time is dominated by repeated component fetches.
- **Hidden permission branch:** permission check inside `<ActionMenu>` reads stale local role state after a backend role change, so the menu still renders privileged actions that should be evaluated by the page or feature owner.
- **State hoisted too high:** state lifted to `App` root for two pages causes every component in the tree to re-render on a filter input keystroke, including a list of 500 items.
- **Premature shared API:** shared `<DataTable>` is extracted before requirements are stable; two consumers diverge and the component accumulates 40 props and feature-specific branches.
- **Excessive depth:** component depth of 7 levels means a delete-button bug requires opening seven files to find the action owner.
- **Provider-coupled feature section:** a component cannot render without router, query client, feature flag provider, and global store, so stories and tests mock the app shell instead of the component boundary.
- **Validation blind spot:** a split is approved because file size decreased, but no story, test, validator command, report, or residual-risk owner proves the new boundaries render, recover, or preserve permissions.

# Output Contract

Return a component decomposition map with:

- `mode_selected` (new page/screen, giant component decomposition, shared component proposal, state/side-effect ownership, permission-sensitive decomposition, testability boundary)
- `source_evidence` (current route/page files, component files, stories, tests, design-system components, API hooks, state stores, repository graph, memory/trajectory evidence inspected with freshness limits)
- `page_owner` (component name; responsibility; route context; permission gate location; data-fetch orchestration)
- `component_tree` (hierarchy: page → feature sections → shared primitives; depth ≤ 4 for most features)
- `component_responsibilities` (per component: one-sentence responsibility; owned state; data inputs as props; emitted callbacks; side effects)
- `ownership_boundaries` (orchestrator vs feature section vs presentational primitive vs hook/container vs layout; what each must not own)
- `state_ownership` (per state value: owner component; lifting justification if above local; global/URL state rationale)
- `data_fetching_locations` (which component triggers each fetch; query key for cache deduplication; loading/error/empty state handling)
- `permission_check_locations` (which components evaluate permissions; must be page/feature level — not in presentational primitives)
- `side_effect_boundaries` (navigation, mutation, analytics, cache invalidation, timers, subscriptions, external APIs, and where they are allowed)
- `shared_component_criteria` (components proposed for reuse: minimum 2 confirmed consumers; stable props contract; design-system alignment)
- `reuse_and_placement_decisions` (feature-local/shared/design-system/hook/layout placement; direct reuse, extension, composition, extraction, or new component justification)
- `graph_and_memory_decisions` (current consumers, caller/callee or parent/child component graph, reused project pattern, stale memory rejected or accepted)
- `accessibility_states` (per interactive component: idle/loading/disabled/error/success states with ARIA attributes)
- `test_boundaries` (per component: test isolation requirement; Storybook story feasibility; mock requirements)
- `boundaries_not_to_cross` (e.g., no data fetching in primitives; no navigation in form fields; no auth checks in display components)
- `changed_component_to_validation_map` (each component, state owner, side effect, permission branch, shared extraction, or story/test obligation mapped to validator/test or residual risk)
- `validation_obligations` (per changed component boundary: validator command or manual artifact/report, expected proof, exit code or review status, freshness after final component-map edit, and not-run residual owner)
- `handoff_boundaries` (what belongs to IA, state management, interaction states, design system, API integration, frontend testing, security, or implementation)
- `evidence_limits` (what was not inspected, no live render, no Storybook/browser run, no accessibility scan, no real component graph, or no source tests)

# Evidence Contract

- **Boundaries inspected:** name route/page/component/story/test/design-system files, providers, hooks, state stores, API fixtures, and generated or not-inspected surfaces that shaped the map.
- **Reuse and placement rationale:** explain direct reuse, feature-local placement, shared extraction, design-system placement, hook/container extraction, or rejected wrapper/common placement.
- **Behavior preservation:** for an existing component split, state old visible behavior, permissions, state reset behavior, and side effects preserved or intentionally changed.
- **Validation evidence:** map decisions to Storybook stories, component tests, integration tests, accessibility checks, validator commands, exit codes, reports, screenshots, artifacts, or explicitly unrun validators with owners.
- **What evidence proves:** the inspected source and validation prove the proposed component ownership, state/effect placement, and test/story boundary for the named files only.
- **What evidence does not prove:** live browser behavior, production API contracts, design-system approval, accessibility certification, performance under load, or real user success unless those validators or artifacts were specifically inspected.
- **Graph and memory evidence:** parent/child edges, consumers, providers, callbacks, shared primitives, and previous patterns are selectors only until current source, stories, tests, and validation confirm freshness.
- **Residual risk and next gate:** name unresolved source gaps, not-run validators, stale graph or memory evidence, and the next owner such as `frontend-testing`, `interaction-state-modeling`, `state-management-design`, or `security-privacy-gate`.

# Benchmark Coverage

Professional decomposition covers responsibility, state ownership, data fetching, side-effect placement, permission visibility, component graph depth, reuse pressure, design-system alignment, accessibility states, Storybook/test isolation, and validation mapping. A component split that only changes file size or folder shape is incomplete.

# Routing Coverage

Route here when the primary question is component responsibility, page ownership, state/effect placement inside a page, shared component extraction, or testability of the component tree. Hand off to `information-architecture` for navigation/content structure, `interaction-state-modeling` for complete UI state transitions, `state-management-design` for global/server/form/auth state architecture, `design-system-rules` for component variants/tokens/accessibility governance, `frontend-api-integration` for request lifecycle, `frontend-testing` for executable behavior proof, and `security-privacy-gate` when permission decomposition can leak privileged actions or data.

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
11. Selected mode, source evidence, component graph, and decomposition boundaries are explicit.
12. Repository graph, project memory, and execution trajectory evidence are current-source-confirmed or marked not verified.
13. Every changed component, state owner, side effect, permission branch, shared extraction, story, or test obligation maps to validation evidence, validator command/artifact/report status, freshness after the final edit, or a named residual risk.
14. Handoff boundaries and evidence limits are named so decomposition evidence is not over-claimed as navigation design, global state architecture, design-system approval, accessibility certification, or browser-tested behavior.

# Used By

- frontend-change-builder
- experience-impact-modeler

# Handoff

Hand off to `information-architecture` when page grouping, navigation labels, or task hierarchy is unresolved; `interaction-state-modeling` for loading/error/empty/disabled/permission-denied state matrices; `state-management-design` for global/server/form/auth state source decisions and invalidation rules; `frontend-api-integration` for request lifecycle, cache keys, retry, and cancellation; `design-system-rules` for shared component governance, variants, tokens, and accessibility semantics; `frontend-testing` for component behavior, Storybook, role/state, and accessibility proof; and `security-privacy-gate` when permission placement can leak privileged actions or data.

# Completion Criteria

The capability is complete when **every component has a single explicit responsibility, state ownership is defined at the nearest correct owner, presentational components are free of side effects and authorization logic, data fetching is co-located with data consumers, and every component is independently testable without global providers or network mocks**.
