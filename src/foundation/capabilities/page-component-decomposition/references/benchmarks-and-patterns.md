# Page Component Decomposition Benchmarks And Patterns

Load this reference when page, feature, hook/container, layout, or shared-component ownership is unclear. Do not load it for a small local component whose responsibility and state/effect owner are already explicit.

## Responsibility Boundaries

| Boundary | Owns | Reject when | Required proof |
| --- | --- | --- | --- |
| Page/route orchestrator | Route params, permission/readiness, top-level data coordination, layout, cross-section submit. | It accumulates domain calculations, field rules, or primitive visual behavior. | Route contract, data/effect map, and contained failure states. |
| Feature section | One user workflow such as a form, list, table action group, or wizard step. | It coordinates unrelated features or global navigation. | Named task, inputs/events, local state, and behavior test boundary. |
| Hook/container/operation owner | Fetch, cache, mutation, subscription, timer, and cleanup orchestration. | It renders UI or hides domain/permission policy. | Lifecycle states, cancellation, invalidation, cleanup, and failure evidence. |
| Presentational primitive | One stable display or interaction contract. | It fetches, navigates, authorizes, reads env/global stores, or contains business rules. | Props/events, semantic output, states, and accessibility proof. |
| Layout | Structural regions, slots, responsive order, and layout-only state. | Data dependencies or business state leak into it. | Slot contract, responsive/focus order, and replacement boundary. |
| Shared component | A current recurring semantic interaction owned across surfaces. | Only visual similarity or speculative consumers justify extraction. | Real consumers, small product-state API, owner, stories/tests, and lifecycle. |

For local component state, choose the nearest owner containing its current readers and writers. Lift to a common feature owner when real sibling coordination requires it; use feature context when tree depth—not unclear ownership—is the issue. Server-owned state stays in the current query/cache owner, URL-addressable state stays in route state, and persisted/cross-route state is routed to `state-management-design`.

## Failure And Proof

Reject visual-box-only splitting, shared “utils/components” without a semantic owner, and primitives that import router/store/API/analytics/env. Also reject custom hooks returning UI, duplicate server truth in local state, and state placed so high that resetting it requires unrelated unmounting.

Inspect current components, imports, effects, stories/tests, design-system candidates, and actual consumers. Source structure cannot prove runtime render cost, subscription behavior, accessibility, or future reuse; a second consumer is evidence only when the semantic contract really matches.

Route state lifetime/cache/persistence to `state-management-design`, permission policy to `permission-boundary-modeling`, shared visual governance to `design-system-rules`, API lifecycle to `frontend-api-integration`, and behavior/accessibility proof to `frontend-testing`.
