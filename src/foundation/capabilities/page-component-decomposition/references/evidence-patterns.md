# Page Component Decomposition Evidence Patterns

Use this reference when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, report artifacts, tool permission boundaries, or a changed-component-to-validation map. Keep it as an evidence map, not a second component tutorial.

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
| Graph or memory claim is fresh | Prior pattern source/date, current component graph, consumers, stories, tests, design-system contract, and accepted/rejected freshness verdict | Reuse or rejection of a remembered pattern is source-backed | Uninspected branches, old generated artifacts, or abandoned prototypes are current |

## Graph, Memory, And Execution Reconciliation

- Treat repository graph, project memory, prior stories, old screenshots, generated components, and execution trajectory as discovery inputs until current source confirms them.
- Accept prior "this pattern is reusable", "this story covers it", "this provider is required", or "this component is design-system-owned" claims only when current component source, consumers, stories, tests, and design-system files still match.
- Mark evidence stale after edits to component APIs, hooks, routes, providers, state stores, query keys, fixtures, stories, snapshots, accessibility behavior, validation commands, or build outputs.
- Record inspected and skipped surfaces: route/page files, components, hooks, stores, providers, stories, tests, design-system components, API fixtures, generated artifacts, browser screenshots, and accessibility reports.
- Map every final decomposition claim to a source path, story/test path, validator command, screenshot/report artifact, owner review, or explicit not-run residual risk.

## Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, graph search, report inspection, and markdown validation | Read-only local shell action; cite searched paths and avoid full output dumps |
| Local component tests, Storybook checks, accessibility scans, visual diffs, validators, and builds | State-mutating only for reports, caches, screenshots, snapshots, dist/build artifacts, or local fixtures; cite command, exit code, artifact path, sandbox, write scope, and cleanup |
| Snapshot update, story artifact refresh, fixture regeneration, or generated client refresh | State-mutating development action; record source-of-truth input, generated output owner, diff review, and rollback path |
| Browser cloud, production analytics, session replay, customer screenshots, or connector export | High-risk or connector-scoped action; require permission, redact tenant/user/secret-bearing values, set retention limit, and state residual proof limits |

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

Block completion when component boundaries are justified only by file size, shared extraction has fewer than two current stable consumers, permission checks remain hidden in primitives, presentational components require router/store/network providers, graph or memory evidence is reused without current-source confirmation, changed components lack story/test/validator mapping or not-run owner, or artifact-writing commands lack write-scope and rollback disclosure.
