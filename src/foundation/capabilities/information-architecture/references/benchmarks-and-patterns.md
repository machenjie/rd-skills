# Information Architecture Benchmarks And Patterns

Use this reference when `information-architecture` output needs more detail than the `SKILL.md` body should carry efficiently. Keep the main skill body focused on routing, evidence, output contract, and gates; use this file for benchmark anchors, navigation pattern selection, organization schemes, validation methods, graph/memory/trajectory coupling, and anti-pattern review.

## Contents

- Benchmark Anchors
- Navigation Pattern Selection Matrix
- Organization Scheme Selection
- Role Visibility And Restricted Destination Matrix
- Empty And Unavailable Structure Matrix
- IA Validation Methods
- Graph, Memory, And Trajectory Coupling
- Review Questions
- Anti-Patterns To Reject
- Handoff Boundaries

## Benchmark Anchors

- Jesse James Garrett, The Elements of User Experience: IA sits at the structure layer between strategy/scope and skeleton/surface; do not confuse structure with visual layout.
- Peter Morville and Louis Rosenfeld, Information Architecture for the World Wide Web: evaluate content, context, and users; cover organization, labeling, navigation, and search systems.
- Richard Saul Wurman's LATCH principle: organize by Location, Alphabet, Time, Category, or Hierarchy according to the user's task.
- Card sorting: open card sorts discover mental models; closed card sorts validate whether proposed categories match user expectations.
- Tree testing: validates findability without visual design bias; primary tasks should have a declared directness or success target.
- First-click testing: the first navigation choice strongly predicts whether users complete a task.
- Nielsen usability heuristics and information scent: labels, headings, and link text must give strong relevance cues.
- WCAG 2.2 navigation criteria: page titles, link purpose, focus order, headings/labels, and multiple ways to find content affect IA quality.
- Mobile navigation guidance: bottom navigation is only for a small set of primary destinations; large taxonomies need other patterns.
- Operational UX practice: support, admin, audit, diagnosis, and recovery tasks need explicit IA, not afterthought menu placement.

## Navigation Pattern Selection Matrix

| Pattern | Best for | Typical item budget | Depth | Avoid when |
| --- | --- | --- | --- | --- |
| Top navigation bar | Global desktop sections. | 5-7 | 1-2 | Mobile primary nav or large product suites. |
| Left sidebar | Product or section navigation with repeated use. | 7-15 | 2-3 | Small apps with few sections or narrow mobile screens. |
| Bottom navigation | Mobile primary destinations. | 3-5 | 1 | More than 5 destinations or deep hierarchy. |
| Tabs | Peer sections within one page/surface. | 3-8 | 1 | Parent/child hierarchy or unrelated sections. |
| Mega menu | Broad catalog taxonomy with many groups. | Many, grouped | 2-3 | Small B2B tools or task workflows. |
| Breadcrumb | Hierarchical context and recovery. | N/A | Any | Flat structures with no meaningful parent. |
| Search/filter | Known-item lookup, large lists, or >3-level structures. | N/A | N/A | When users must browse unknown concepts first. |
| Progressive disclosure | Complex tasks where users need staged structure. | N/A | N/A | When all information is required for comparison. |

## Organization Scheme Selection

| User task | Strong scheme | Required IA evidence | Watchout |
| --- | --- | --- | --- |
| Find a known item. | Alphabet, search, ID lookup, or recent items. | Search scope, identifiers, filters, empty/no-result behavior. | Do not bury known-item lookup in category hierarchy. |
| Browse and compare options. | Category hierarchy plus faceted filters. | Category label source, card sort or domain expert evidence, facet ownership. | Categories that mirror database enums may not match user vocabulary. |
| Understand what happened over time. | Time-based or timeline structure. | Default order, date filters, timezone/currency owner if relevant. | Activity logs without filters become forensic dead ends. |
| Complete a multi-step task. | Task flow or wizard IA. | Entry, progress, back/re-entry, and handoff to user-flow-modeling. | IA cannot substitute for flow branch design. |
| Monitor and act on current state. | Status, urgency, owner, queue, or priority grouping. | Operational role, status definitions, bulk actions, escalation path. | Dashboard vanity metrics can hide action queues. |
| Administer users or systems. | Separate admin/operational IA or clearly scoped admin section. | Admin tasks, audit needs, impersonation/support paths, role visibility. | Copying end-user IA with extra items buries operational tasks. |
| Diagnose or audit. | Entity relationship plus timeline and evidence trails. | Source-of-truth owner, linked objects, breadcrumbs, export/audit restrictions. | Audit links can leak privileged data if role visibility is vague. |

## Role Visibility And Restricted Destination Matrix

| Visibility | Use when | User experience | Evidence needed | Risk |
| --- | --- | --- | --- | --- |
| Visible | User can access and act. | Normal nav item and direct route. | Role/action permission confirmation. | Low if authorization is still server-side. |
| Locked | User may know the feature exists but lacks access. | Disabled or locked item with access reason and request path. | Role matrix, request-access owner, non-sensitive feature decision. | Overly specific copy can reveal sensitive role details. |
| Hidden | User should not know feature/resource exists. | Nav item absent; direct route uses non-leaking unavailable/not-found state. | Sensitivity reason, confidential/beta/regulatory rationale. | Users with legitimate links can hit confusing dead ends without recovery. |
| Contextual | Item appears only when a relevant object/state exists. | In-object link, related action, breadcrumb, or contextual menu. | Object relationship and empty/unavailable behavior. | Users may not discover cross-module tasks. |

## Empty And Unavailable Structure Matrix

| State | Meaning | User action | IA requirement |
| --- | --- | --- | --- |
| First-run empty | Nothing exists yet. | Create, invite, import, connect, or learn next step. | Explain what belongs here and why it is empty. |
| True empty | The dataset legitimately has no items. | Create or leave stable. | Avoid implying failure. |
| Filtered empty | Items may exist, but filters hide them. | Clear filters or change search. | Preserve filter context and offer reset. |
| No access | Items may exist but caller lacks access. | Request access or navigate away. | Do not leak sensitive details. |
| Archived/deleted | Item existed but is unavailable. | Recover, view archive, or return to parent when allowed. | Direct link recovery and breadcrumb. |
| Feature unavailable | Tenant, plan, flag, maintenance, or rollout blocks access. | Upgrade, request enablement, wait, or return. | Distinguish from missing permission when safe. |
| Dependency failure | Data source failed. | Retry or contact support with trace. | Hand off to interaction-state-modeling for UI state. |

## IA Validation Methods

| Method | Use for | Good evidence | Limits |
| --- | --- | --- | --- |
| Open card sort | Discover how users group concepts. | Cluster patterns, label vocabulary, participant role notes. | Does not validate final navigation success. |
| Closed card sort | Validate proposed group labels. | Misplaced cards and confusing categories. | May miss route/deep-link problems. |
| Tree test | Validate findability in a hierarchy. | Success/directness/time per task. | No visual design or content layout signal. |
| First-click test | Validate first navigation choice. | First click, confidence, misroutes. | Does not prove completion of later steps. |
| Support/analytics review | Find real friction and dead ends. | Current date range, event definitions, support taxonomy. | Stale or poorly tagged signals can mislead. |
| Expert review | Catch obvious hierarchy, label, or permission issues quickly. | Heuristic findings mapped to tasks. | Not a substitute for user validation. |

## Graph, Memory, And Trajectory Coupling

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current nav files, route owners, breadcrumbs, labels, permission wrappers, empty states, tests, and generated links were inspected. | Graph proximity is treated as proof that users can find or complete tasks. |
| Project memory | Prior IA decision names unchanged paths, labels, roles, and date/freshness evidence. | Memory predates route rename, role model change, support workflow update, or taxonomy migration. |
| Execution trajectory | IA validation or build/test output ran after the final content/routing edit. | Evidence predates final edit or covers only one route/happy path. |
| Analytics/support signal | Signal includes current route/label names, date range, user segment, and observed failure. | Signal is anecdotal, stale, or mapped to old taxonomy. |
| User research | Participant segment matches the target user and task. | Research was for a different role, product tier, locale, or workflow. |

Strong outputs state which graph or memory evidence was accepted, rejected, or left unknown.

## Review Questions

1. What primary tasks are users trying to complete, and which are most frequent or critical?
2. Which labels come from users, domain experts, analytics, support, or unverified product assumptions?
3. Which internal terms, database nouns, service boundaries, or team names were rejected?
4. What is the maximum navigation depth, and what fallback exists if it exceeds 3 levels?
5. Which destinations are visible, locked, hidden, or contextual for each role?
6. What happens when a user opens a restricted destination from email, notification, bookmark, or search?
7. Which empty states differ: first-run, true empty, filtered empty, no access, archived, unavailable, failure?
8. Which cross-module handoffs preserve context, breadcrumb, object relationship, and return path?
9. Which admin, support, audit, diagnostic, or operational tasks need separate structure?
10. Which validation method proves findability, and what remains unverified?

## Anti-Patterns To Reject

| Anti-pattern | Why it fails | Required correction |
| --- | --- | --- |
| Navigation item per database table. | Users think in tasks, not storage entities. | Group by task and user vocabulary. |
| Service/team boundaries as IA. | Cross-module tasks require context switching. | Integrate around the user's job to be done. |
| Internal labels such as principals, artifacts, ledgers, or jobs. | Users cannot recognize their task. | Run vocabulary audit and use domain language. |
| Everything unauthorized is hidden. | Direct links and permission changes produce dead ends. | Use visible/locked/hidden policy with direct-entry behavior. |
| Generic "no data" everywhere. | Users do not know whether to create, clear filters, request access, or retry. | Split structural empty states and CTAs. |
| Deep hierarchy without search/filter. | Users lose orientation and rely on browser back. | Keep depth <= 3 or add findability fallback. |
| Mobile bottom nav with too many destinations. | Tap targets and wayfinding degrade. | Limit primary destinations and move secondary items elsewhere. |
| Admin IA equals product IA plus extra menu items. | Operational tasks are buried. | Design admin/support/audit IA from operational tasks. |
| Cross-module link without return context. | Users lose task position. | Define breadcrumb/back behavior and preserved object context. |
| Reused old taxonomy from memory only. | Stale labels and permissions persist. | Confirm current source, graph, roles, and validation freshness. |

## Handoff Boundaries

- Use `user-flow-modeling` for ordered entry, branch, back, retry, cancel, and exit behavior.
- Use `routing-navigation-design` for URL structure, route guards, redirects, history, direct-entry states, and public route migration.
- Use `interaction-state-modeling` for single-screen loading, empty, error, disabled, no-access, stale, and retry states.
- Use `page-component-decomposition` for page/component ownership, layout slots, state/effect placement, and component testability.
- Use `permission-boundary-modeling` or `authentication-authorization` for object/action authorization policy.
- Use `design-system-rules` for visual navigation components, tokens, responsive styling, and accessibility implementation details.
- Use `frontend-testing` and `quality-test-gate` for executable findability, route, direct-entry, accessibility, or regression proof.
