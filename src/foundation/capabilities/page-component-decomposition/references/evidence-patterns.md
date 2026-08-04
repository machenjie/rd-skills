# Page Component Decomposition Evidence Patterns

Use this reference when closure depends on repository inspection, prior task evidence, observable action sequence, validation freshness, command output, report artifacts, tool permission boundaries, or a changed-component-to-validation map. Keep it as an evidence map, not a second component tutorial.

## Component Decision-To-Evidence Map

| Decomposition claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Page owner is correct | Route/page source, user task, route params, permission gate, data source, and orchestration responsibility | The inspected page has a named owner for the declared workflow | Navigation IA, backend contract, or every browser behavior is proven |
| Component responsibility is single-purpose | Component source, one-sentence responsibility, inputs, callbacks, owned state, side effects, and replacement boundary | The inspected component has a reviewable responsibility | Future feature growth or uninspected siblings stay clean |
| State owner is nearest correct owner | Readers/writers, validation/reset behavior, sibling coordination, URL/global/server-state decision, and owner component | The inspected state has an explicit ownership rationale | Performance, all rerender paths, or persistence behavior is fully proven |
| Side effects are correctly placed | Fetch/mutation/navigation/analytics/timer/subscription inventory, hook/container/page owner, cleanup rule, and cache invalidation path | The inspected side effects are not hidden in primitives | External API behavior or all cancellation cases are safe |
| Permission placement is visible | Role/tenant/owner source, allowed/denied/disabled/hidden branches, primitive props, and role fixture/test obligation | UI authorization decisions are visible at page/feature level | Backend authorization or every object-level permission path is enforced |
| Shared extraction is justified | Current consumer list, stable props contract, owner, design-system alternatives, Storybook/doc obligation, and rejected feature-local placement | Shared placement has current reuse pressure | Future API stability or design-system approval is guaranteed |
| Test or story boundary is credible | Story/test path, provider/router/network requirements, fixture owner, accessible states, command/report, and exit code or not-run owner | The named component boundary has a validation obligation | Full live browser behavior, visual parity, or accessibility certification is complete |
| Prior source or task evidence claim is fresh | Prior pattern source/date, current component graph, consumers, stories, tests, design-system contract, and accepted/rejected freshness verdict | Reuse or rejection of a remembered pattern is source-backed | Uninspected branches, old generated artifacts, or abandoned prototypes are current |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, prior stories, old screenshots, generated components, and observable action sequence as discovery inputs until current source confirms them.
- Accept prior reuse or ownership claims only while current component source, consumers, stories, tests, and design-system files still match. Examples include "this pattern is reusable", "this story covers it", "this provider is required", and "this component is design-system-owned".
- Mark evidence stale after edits to component APIs, hooks, routes, providers, state stores, query keys, fixtures, stories, snapshots, accessibility behavior, validation commands, or build outputs.
- Record inspected and skipped surfaces: route/page files, components, hooks, stores, providers, stories, tests, design-system components, API fixtures, generated artifacts, browser screenshots, and accessibility reports.
- For each page, component, state-owner, side-effect, permission, extraction, or test-boundary claim made in the final handoff, name its current source or validation artifact, owner review, or explicit not-run residual risk.

## Tool Permission Boundary

- When the task refreshes a snapshot, story, fixture, or generated client, record the source-of-truth input, generated owner, reviewed visual or contract diff, and applicable rollback path; disclose any unavailable proof.
- Browser-cloud captures, session replay, analytics, and customer screenshots require permission, tenant/user redaction, a retention limit, and a device or viewport coverage limit.

## Handoff Evidence Shape

```yaml
page_component_decomposition_evidence_closure:
  inspected_surfaces: []
  accepted_prior_claims: []
  rejected_or_stale_claims: []
  changed_component_to_validation_map: []
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    redaction: ""
  what_remains_unproved: []
  residual_component_risk: []
  next_gate: ""
```

## Blocking Conditions

Block completion when boundaries rely only on file size, shared extraction lacks stable consumers, permission checks hide in primitives, or presentation requires infrastructure providers. Also block stale prior evidence, changed components without validation ownership, and artifact-writing commands without write-scope and rollback disclosure.
