# Page Component Decomposition Benchmarks And Patterns

Use this reference when page-component-decomposition output needs more detail than the `SKILL.md` body can carry efficiently. Keep the main skill body focused on routing, ownership evidence, output contract, and quality gates.

## Benchmark Anchors

- React "Thinking in React" for component hierarchy, single responsibility, and state co-location.
- Presentational/container separation adapted for hooks: keep "how it looks" separate from "how it works" without forcing class-era containers.
- State co-location guidance: keep state as close as possible to the readers and writers that can validate, update, and reset it.
- Atomic Design taxonomy for primitives, groups, feature sections, layouts, and page instances when a design system uses that vocabulary.
- TanStack Query, SWR, and RTK Query for query co-location, deduplication, stale data, retry, and cache ownership.
- Storybook component-driven development for independently renderable states and props-only stories.
- Testing Library behavior-first philosophy for public behavior and accessible queries instead of private implementation details.
- WCAG adaptable and name/role/value requirements for meaningful structure, status, disabled, error, and interactive states.

## Component Responsibility Classification

| Component type | Owns | Must not contain | State ownership | Test or story focus |
| --- | --- | --- | --- | --- |
| Page orchestrator | Route context, URL params, permission gate, data-fetch coordination, top-level layout, cross-section submit. | Domain calculations, primitive UI decisions, field-level validation details. | URL/global/server readiness, cross-section state. | Route guard, permission rendering, load/error/empty orchestration. |
| Feature section | One feature workflow such as form, list, wizard step, table action group, or settings section. | Cross-feature coordination or unrelated page navigation. | Local feature state, lifted only when sibling coordination requires it. | Workflow behavior, submission, validation, section states. |
| Presentational primitive | Single UI interaction or display pattern such as button, input, modal, badge, card row. | Data fetching, permission decisions, navigation, business logic. | No state or minimal local interaction state. | Props to accessible render output and callbacks. |
| Hook or container | Data fetching, cache management, derived state, mutation orchestration, subscriptions. | UI rendering or visual layout decisions. | Server/global/cache state. | Loading/error/success transitions, invalidation, cleanup. |
| Layout | Structural slots, regions, responsive container, header/sidebar/grid placement. | Data dependencies, business rules, state transitions. | None or layout-only UI state. | Slot composition, responsive behavior, focus order. |
| Shared design-system component | Stable reusable interaction contract across product surfaces. | Feature-specific flags, page-specific data, business vocabulary. | Component-internal UI state only. | Variant behavior, accessibility contract, Storybook matrix. |

## State Ownership Decision Tree

```text
Does only one component read and update this state?
  YES -> keep it local.

Do sibling components read or update the same state?
  YES -> lift to the nearest common parent.
  YES and the tree is deep -> use feature-scoped context after owner is known.

Does the state need to persist across routes or browser sessions?
  YES -> route/global/persisted state design belongs to state-management-design.

Is the state server-derived?
  YES -> keep it in the server-state cache or query hook, not duplicated local state.
  YES and multiple components need it -> share by query key or feature-scoped owner.

Is the state URL-addressable or part of back-button/share-link behavior?
  YES -> use route/search/path state; do not hide it in component local state.

Does reset require unmounting an unrelated parent?
  YES -> state is probably too high.
```

## Decomposition Review Questions

1. Can the component responsibility be stated in one sentence without "and"?
2. What user task or page section owns this component?
3. Which state values does it read, write, validate, reset, or persist?
4. Which side effects does it trigger: fetch, mutate, navigate, analytics, timer, subscription, cache invalidation?
5. Which props are data inputs and which callbacks are events?
6. Can it render in Storybook or a component test with props only?
7. Which parent or child would change if this component were replaced?
8. Is this feature-local, shared within a feature, or design-system-level?
9. Are there at least two stable consumers before shared extraction?
10. Which states, roles, permissions, and failures need tests?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| `OrderPage.tsx` fetches data, validates form, renders table, handles payments, and navigates after submit. | One component owns too many responsibilities and cannot be tested at the right boundary. | Split orchestrator, feature sections, presentational primitives, and hooks/containers. |
| `<Button disabled={!user.roles.includes("admin")}>` | Authorization decision is hidden inside a primitive and duplicated across UI. | Compute permission at page/feature level; pass `disabled`, `visible`, or action eligibility props. |
| `<UserCard>` fetches its own user data. | Cannot render without network/provider and creates duplicate fetch risk in lists. | Fetch in page/feature/hook owner; pass `user` and callbacks to card. |
| Shared `<SearchPage>` extracted for one current consumer. | Future-proofing creates a generic API before stable reuse exists. | Keep feature-local until another real consumer has overlapping needs. |
| Prop drilling theme/auth/query data through many unrelated levels. | Intermediates become coupled to data they do not own. | Use feature context, design-system provider, or query cache only after ownership is explicit. |
| Component split by visual boxes only. | File count increases but behavior, state, and side effects remain unclear. | Split by responsibility, ownership, and test boundary. |
| Custom hook renders UI or returns JSX. | Behavior and rendering boundaries are blurred. | Use hooks for behavior/data and components for rendering. |
| Presentational primitive imports router, store, query client, analytics client, or env. | Primitive becomes unportable and hard to test. | Move side effects to orchestrator/container and pass props/callbacks down. |

## Shared Component Extraction Rules

Shared extraction is justified only when current evidence proves:

- At least two stable consumers exist now, not only imagined future use.
- Consumers share the same semantic responsibility, not just visual similarity.
- Props contract can stay small and product-state-driven.
- Design-system component or composition cannot already satisfy the need.
- Owner, Storybook stories, accessibility obligations, and deprecation path are named.
- Feature-specific vocabulary, permissions, API data, and business rules remain outside the shared component.

Reject extraction when it only avoids duplication of a small layout, anticipates future needs, introduces boolean feature flags, or would require the shared component to import feature modules.
