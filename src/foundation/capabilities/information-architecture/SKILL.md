---
name: information-architecture
description: Defines page, module, navigation, and content structure around user tasks rather than internal database or implementation structure.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "07"
changeforge_version: 0.1.0
---

# Mission

Shape information, navigation, and module structure so **users can locate, understand, and act on what matters to them** — organizing around user tasks and mental models rather than internal database structure, service boundaries, or technical implementation naming — accounting for role-based visibility, empty states, cross-module handoff, and operational user needs.

# When To Use

Use this capability when a change: adds or restructures pages, navigation sections, or modules; introduces new content types that need placement in the existing hierarchy; changes how users discover features (menu, search, deep-link); redesigns navigation for a new user segment (onboarding, admin, support); adds role-based visibility requirements that affect navigation structure; or introduces new cross-module task flows where users must move between modules to complete a single goal.

# Do Not Use When

Do not use this capability to mirror database table names in navigation (technical nouns do not equal user tasks). Do not use it to expose internal service or microservice boundaries in the product UI — service decomposition is an engineering concern, not a user navigation concern. Do not use it to specify visual styling, component-level layout, or interaction patterns — those belong in `design-system-rules` and `page-component-decomposition`.

# Stage Fit

Use during experience-definition, implementation-planning, coding, bug-fix, debugging, code-review, refactoring, testing, release-readiness, and final handoff when page/module grouping, navigation hierarchy, labels, search/findability, role visibility, empty structural states, cross-module handoffs, or admin/operational task discoverability are changing. In planning, define task vocabulary, organization scheme, visibility policy, deep-link and empty-state structure, validation method, and handoff boundaries before route or component implementation. In coding and refactoring, keep routes, labels, breadcrumbs, empty states, search/filter placement, and permission visibility aligned with the accepted IA instead of letting screens grow local structure. In debugging, separate IA findability defects from route guard, component state, permission, analytics, and copy defects before changing structure. In code-review and testing, reject database-noun IA, service-boundary leakage, hidden permission dead ends, stale project-memory taxonomy, and repository-graph claims that are not confirmed against current screens, routes, labels, analytics/support signals, and tests. In release-readiness and final handoff, require fresh validation evidence and residual risk after the final label, route, visibility, empty-state, search/filter, or handoff edit. Hand off when the primary question is ordered flow behavior, route guard mechanics, component composition, permission policy, visual styling, or executable frontend tests.

# Non-Negotiable Rules

- **Organization is task-first, not noun-first.** Navigation menus that list database entities (Users, Orders, Products, Events) without task framing fail users who think in terms of goals (Manage team access, Track a delivery, Update pricing). Every navigation item must answer: "What does the user want to do from here?"
- **Separate user-facing concepts from storage models.** The fact that a "subscription" is stored as three tables (plans, subscriptions, billing_cycles) does not mean the navigation should have three entries. Merge, abstract, and rename to match user vocabulary.
- **Labels must match user vocabulary, not internal terminology.** Conduct a vocabulary audit: what does the user call this? "Ledger entries" → user says "Transactions." "Principals" → user says "Team members." Wrong labels increase task completion time and call center volume.
- **Navigation depth must not exceed 3 levels without search.** Beyond 3 levels of hierarchy, users lose orientation. Miller's Law (7±2 items per level) and progressive disclosure are the mitigations for breadth. Depth beyond 3 requires a search or filter mechanism.
- **Permission-aware visibility: show restricted items as locked, not invisible.** Completely hiding a navigation item for which the user lacks permission creates a "where did it go?" effect when permissions change. Recommended pattern: show item with a lock icon and tooltip explaining access requirement. Exception: items the user should not know exist (confidential feature, beta, regulatory restriction) may be fully hidden with clear documentation.
- **Every list, table, or card view must have a designed empty state.** An empty state without a call-to-action is a dead end. "No items found" is insufficient. Include: what goes here, why it is empty, what to do next (create first item, invite a team member, import data).
- **Cross-module handoff points must be explicit.** When a task spans two modules (e.g., Order → Customer; Invoice → Project), define the exact handoff: what link or action moves the user; what context is preserved (breadcrumb parent, back navigation); whether it is a deep link or a full navigation reset.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Task taxonomy and labels | New section, renamed nav, new content type, or user vocabulary mismatch. | Task-first grouping, label audit, content/context/user fit. | Primary tasks, user segment, current labels, vocabulary source, rejected internal terms. | `scenario-decomposition`, `user-role-identification` | Database table mirroring. |
| Navigation hierarchy | New or reorganized global/section nav, sidebar, tabs, mobile nav, breadcrumb, or search path. | Depth, breadth, pattern fit, wayfinding, fallback search/filter. | Current route/nav inventory, max depth, target device, deep-link and breadcrumb behavior. | `routing-navigation-design`, `page-component-decomposition` | Component styling. |
| Role and permission visibility | Permission-specific nav, locked destinations, confidential feature, admin/support view. | Visible/locked/hidden policy and non-dead-end restricted access. | Role matrix, sensitivity reason, request-access or non-leaking recovery path. | `permission-boundary-modeling`, `security-privacy-gate` when sensitive | Server authorization design. |
| Empty and unavailable structure | Empty list, filtered-empty, first-run, archived, deleted, unavailable, no-access, or no-results states. | Structural meaning, CTA, recovery path, and non-leaking copy. | Surface list, condition split, allowed CTA, reset/retry/request-access path. | `interaction-state-modeling`, `prototype-description` | Generic "no data" copy. |
| Cross-module handoff | Task crosses modules, support/admin handoff, audit trail, object relationship navigation. | Preserved context, back navigation, breadcrumb, source-of-truth owner. | Source/target module, task context, relationship label, return path. | `user-flow-modeling`, `repository-graph-analysis` | Full journey details unless needed. |
| IA validation and migration | Card sort, tree test, first-click test, route/nav migration, analytics/support signal. | Findability proof, changed structure to validation map, evidence limits. | Validation method, task set, target score, current links/routes searched, stale evidence limits. | `quality-test-gate`, `validation-broker` | Visual preference testing. |

# Industry Benchmarks

Anchor against Garrett's UX structure layer, Morville/Rosenfeld organization-labeling-navigation-search systems, Wurman's LATCH organization schemes, card sorting, tree testing, first-click testing, Nielsen information scent and usability heuristics, WCAG navigation and link-purpose criteria, mobile navigation guidance, and task-oriented operational UX practice. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for benchmark anchors, navigation pattern selection, organization scheme decisions, validation methods, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when **information grouping, navigation structure, labeling, and content discoverability** are the primary design concerns. Adjacent routing:

- Prefer `user-flow-modeling` when the primary concern is the ordered path through tasks and decision points.
- Prefer `page-component-decomposition` when the primary concern is component-level layout and implementation structure.
- Prefer `design-system-rules` when the primary concern is visual design tokens, component library, and styling.
- Prefer `permission-boundary-modeling` when the primary concern is who can see and do what, and the authorization model.
- Prefer `experience-impact-modeler` for end-to-end change impact review across user-facing surfaces.

# Proactive Professional Triggers

- **Signal:** a page/module/nav request names database entities, services, internal teams, or implementation nouns as the proposed IA. **Hidden risk:** users follow the wrong task path because product structure mirrors storage or org charts and misses user vocabulary. **Required professional action:** rewrite the IA around primary user tasks and vocabulary. **Route to:** `scenario-decomposition`, `user-role-identification`. **Evidence required:** task map, user segment, internal term rejected, and user label source.
- **Signal:** a new navigation item, section, or tab is added without a current nav/route inventory, depth budget, search fallback, or mobile pattern decision. **Hidden risk:** IA grows by accretion, missing wayfinding rules create inconsistent hierarchy, and findability degrades. **Required professional action:** map hierarchy, pattern, depth, and fallback. **Route to:** `routing-navigation-design`, `page-component-decomposition`. **Evidence required:** current nav/route inventory map, target device, max depth, and search/filter fallback.
- **Signal:** role-based navigation is implemented as "hide it if unauthorized" for every case. **Hidden risk:** hidden destinations and missing recovery create dead ends from notifications, bookmarks, support handoffs, or permission changes. **Required professional action:** define visible/locked/hidden policy and restricted-destination recovery. **Route to:** `permission-boundary-modeling`, `routing-navigation-design`. **Evidence required:** role visibility matrix, sensitivity reason, direct-entry behavior, and request-access or non-leaking recovery.
- **Signal:** empty states are described as generic "no data" across lists, cards, search, filtered views, unavailable resources, and no-access states. **Hidden risk:** users cannot tell whether to create, clear filters, request access, retry, or leave. **Required professional action:** split structural empty meanings and CTAs. **Route to:** `interaction-state-modeling`, `prototype-description`. **Evidence required:** condition matrix, user copy intent, CTA or recovery action, non-leak rule.
- **Signal:** repository graph, project memory, analytics, support tickets, or prior trajectory is used to justify an IA pattern. **Hidden risk:** stale labels, dead links, old support workflows, or outdated permissions become new structure. **Required professional action:** confirm current source, routes, labels, support/admin tasks, and validation freshness before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths/signals, accepted/rejected pattern, freshness limit, validation or residual risk.
- **Signal:** a sitemap, menu list, or IA recommendation changes labels, levels, visibility, empty states, or handoffs without a changed-IA-to-validation map. **Hidden risk:** unverified structure ships without proof that users can find tasks or recover from restricted/dead-end states. **Required professional action:** map every changed IA decision to a tree/card/first-click/repository-route test, expert review artifact, or named residual owner. **Route to:** `information-architecture`, `quality-test-gate`, `validation-broker`. **Evidence required:** changed decision map, validator test or manual review report, freshness after final IA edit, and what remains not verified.

# Risk Escalation Rules

Escalate when: navigation restructuring breaks existing deep links or bookmarks (SEO impact or user bookmark breakage); a navigation change hides a regulated disclosure or compliance-required action (accessibility audit required); permission-hidden navigation creates dead ends in a regulated workflow; an operational user's ability to diagnose failures or access audit trails is reduced; the mobile navigation requires > 5 primary destinations in a bottom nav bar (exceeds thumb reach optimization).

# Critical Details

IA failures are invisible during development because developers navigate by file path, not by user task — and test data is always perfectly formed. Real users face empty states, insufficient permissions, cross-module flows, and task interruptions. Precision failures:

- **Database noun navigation.** Navigation built directly from entity names (Users, Orders, Products, Events, Tasks). Users think "I need to check why this payment failed" — they do not think "I need to visit the Transactions entity." The correct IA: "Payments" section with sub-navigation: Recent, Failed, Refunded, Disputes — organized by task, not by data model.
- **Service boundary leakage.** A microservices architecture has UserService, SubscriptionService, BillingService. Navigation has three separate sections: User Management, Subscription Management, Billing Management. A support agent needs to cancel a user's subscription and issue a refund — requires switching between three sections with no shared context. Correct IA: "Account Management" section that integrates all three for the support task.
- **Wrong label vocabulary.** Admin IA says "Principals" (internal IAM term). Support agents say "Admins" or "Team members." The mismatch increases training cost and errors. Run a vocabulary audit before finalizing labels — ask 5 users to describe the thing, use their words.
- **Hidden permission dead ends.** A user clicks a notification: "Your report is ready." The link leads to a Reports section that is hidden because their role does not have Reports access. User sees a 404 or empty screen. Fix: show Reports section in navigation with a lock icon; deep link lands on "You need [role] to access this" with a request-access CTA.
- **Missing empty states.** A new user onboards and sees the dashboard. Every panel shows "No data." No call-to-action. User does not know what to do next. First-run empty states are product growth touch points — design them as carefully as full states.

### Anti-examples

| Anti-pattern | Failure |
| --- | --- |
| Navigation item per database table | Users navigate by goal, not by data model; task completion rate drops |
| Service boundaries surfaced as navigation sections | Cross-service tasks require 3 context switches; support agent error rate increases |
| Fully hidden nav items on permission failure | "Where did the Reports menu go?" — confusion, support tickets |
| Empty state = empty container with no text | New user sees blank dashboard; no onboarding path; churn |
| Navigation depth > 4 levels without search | Users abandon; 40%+ use browser back as primary navigation |
| Technical labels in user-facing navigation | Vocabulary mismatch; users do not recognize their task; task failure |
| Admin IA = product IA with extra items | Admin mental model differs; operational tasks buried; incident response slowed |
| Mobile: 7 items in top navigation | Items clip; tap targets too small; keyboard navigation broken |

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 IA selection, stage fit, routing, evidence, output, and gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete IA plan, navigation hierarchy, role visibility table, empty-state structure, search/filter placement, or cross-module handoff. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when detailed benchmark anchors, navigation pattern matrices, organization scheme decisions, validation methods, graph/memory/trajectory coupling, or anti-pattern review is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or minor wording edits where the inline output contract and quality gate are enough.

# Failure Modes

- **Database-noun navigation:** navigation is rebuilt from database entity names; user task completion rate on primary flows drops 25%; usability study required post-launch.
- **Service-boundary portal:** support portal is restructured by service team boundaries; agents must open 3 tabs per ticket; handle time increases 40%; escalation to IA redesign.
- **Permission-hidden deep link:** report page link breaks when Reports section is hidden; users click email notification and see 404; support spike.
- **Dead-end empty dashboard:** new users see no empty-state CTA; 30% churn before completing first action.
- **Overloaded mobile nav:** mobile navigation has 6 bottom items; thumb reach failure; right-side items inaccessible one-handed; WCAG 2.5.5 violation.
- **Copied admin IA:** admin panel mirrors product navigation; "User impersonation" action is buried 4 levels deep; support team spends 10 minutes locating it per ticket.
- **Lost handoff context:** cross-module Order -> Customer handoff has no back-navigation context; user loses order list position and returns to top every time.
- **Internal label mismatch:** internal terminology ("Principals," "Artifacts," "Ledger") is used in UI; users are unfamiliar; task completion rate for new users = 60% vs 85% with user-tested labels.

# Output Contract

Return an information architecture plan with:

- `mode_selected` (task taxonomy and labels / navigation hierarchy / role and permission visibility / empty and unavailable structure / cross-module handoff / IA validation and migration)
- `ia_scope` (user segment, product surface, current structure boundary, included and excluded modules/pages/routes)
- `source_evidence` (current nav/routes/pages, labels, search/filter behavior, roles, analytics/support signals, user research, repository graph, project memory, execution trajectory, tests, and freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, or not verified for each reused taxonomy, nav pattern, role policy, empty state, handoff, support workflow, or validation result)
- `primary_user_tasks` (task name, user segment, frequency, criticality)
- `organization_scheme` (task-first grouping; rationale: LATCH principle applied)
- `navigation_structure` (hierarchy: top-level sections → sub-sections → pages; max depth)
- `navigation_pattern` (top nav / sidebar / bottom nav / tabs / breadcrumb; selection justification)
- `labels` (user-facing label; internal term; vocabulary source: user research / domain expert / tested)
- `role_visibility` (section/page: visible / locked-with-tooltip / hidden; reason for each restriction)
- `empty_states` (for each list/table/card: empty state content; primary CTA)
- `cross_module_handoffs` (source module → target module; link/action; context preserved; back navigation)
- `search_filter` (search scope; filterable dimensions; sort options; for which sections)
- `structural_risks` (fragmented workflows, deep link breaks, permission dead ends, mobile reach issues)
- `validation_method` (card sort / tree test / first-click test; target: > 70% directness on primary tasks)
- `validation_obligations` (for each IA decision: validation type, pass target or review owner, source freshness, and not-run consequence)
- `admin_ia` (if admin users exist: separate admin IA section or explicitly integrated)
- `changed_ia_to_validation_map` (each changed task group, label, nav level, role visibility rule, empty state, handoff, search/filter decision, deep-link behavior, admin/support path, and validation method mapped to evidence/test or residual risk)
- `handoff_boundaries` (what belongs to flow modeling, route design, component decomposition, permission modeling, interaction state, accessibility, copy/content, analytics, or frontend testing)
- `evidence_limits` (what was not inspected or not run: live users, analytics date range, route graph, production roles, browser/mobile behavior, accessibility testing, card sort/tree test, or support workflow validation)

# Evidence Contract

Close an information-architecture output only when it names:

- **Basis:** selected mode, IA scope, target user segment, included/excluded surfaces, and the structural decision being made.
- **Repository evidence:** current nav/routes/pages, labels, breadcrumbs, search/filter behavior, role visibility, empty states, support/admin paths, tests, and source-vs-generated boundaries inspected or explicitly unavailable.
- **Graph, memory, and trajectory evidence:** reused taxonomy, route graph, support workflow, project-memory decision, analytics/support signal, or prior validation accepted, rejected, stale, or not verified with freshness limits.
- **IA proof:** primary tasks, organization scheme, navigation hierarchy, pattern choice, labels and vocabulary source, role visibility policy, empty/unavailable structure, cross-module handoffs, search/filter placement, and admin/operational IA.
- **Validation proof:** changed-IA-to-validation map, validation method, pass target or reviewer, command/manual artifact when available, validation freshness after the final IA edit, and every not-run validation with owner.
- **Handoff evidence:** boundaries to flow modeling, route design, component decomposition, permission modeling, interaction state, accessibility, copy/content, analytics, and frontend testing.
- **What evidence does not prove:** live user success, production analytics, browser/mobile behavior, route guard correctness, authorization enforcement, accessibility certification, or support workflow adoption unless those were specifically inspected or run.

A generic sitemap, menu list, or "organize around users" statement is not sufficient evidence.

# Benchmark Coverage

Improved IA outputs reject common weak patterns: database-noun navigation, service-boundary sections, internal labels, invisible permission dead ends, generic empty states, >3-level hierarchy without search, mobile nav overload, admin IA copied from end-user IA, cross-module links without return context, and stale repository-memory taxonomy. Detailed benchmark anchors, pattern matrices, validation methods, and graph/memory/trajectory coupling belong in references so the body stays efficient.

# Routing Coverage

Route here when content hierarchy, navigation grouping, labels, findability, role visibility, empty-state structure, cross-module wayfinding, search/filter placement, or admin/support IA is primary. Hand off when the primary concern is ordered journey behavior (`user-flow-modeling`), URL guard mechanics (`routing-navigation-design`), component ownership (`page-component-decomposition`), single-screen state (`interaction-state-modeling`), authorization policy (`permission-boundary-modeling` / `authentication-authorization`), visual styling (`design-system-rules`), or executable tests (`quality-test-gate` / `frontend-testing`).

# Quality Gate

The information architecture is complete only when:

1. Selected mode, IA scope, source evidence, and graph/memory/trajectory reuse judgment are explicit.
2. Every navigation section is named in user task vocabulary, not internal noun, database table, service, team, or implementation term.
3. Primary user tasks, user segments, frequency, and criticality drive grouping and priority.
4. Organization scheme is selected with LATCH/task rationale and rejected alternatives when relevant.
5. Cross-module task handoffs are mapped with context preservation, breadcrumb/back-navigation behavior, and source/target owner.
6. Role-based visibility is defined for every section: visible / locked / hidden, with reason and direct-entry behavior.
7. Empty, filtered-empty, first-run, unavailable, archived/deleted, and no-access states are split where they have different user actions.
8. Navigation depth is 3 levels or less, or search/filter/faceted recovery is provided as fallback.
9. Navigation pattern is selected and justified per target device and usage frequency.
10. Labels are audited against user vocabulary with source or residual risk.
11. Deep link behavior is defined for permission-restricted destinations so users do not hit unexplained 404/dead ends.
12. Admin, support, audit, and operational IA are addressed separately when those user segments exist.
13. Each changed task group, label, nav level, visibility rule, empty state, handoff, search/filter decision, and validation method maps to evidence/test or named residual risk.
14. Validation obligations name the validator or manual review artifact, pass target or owner, freshness after the final IA edit, and not-run consequence.
15. Handoff boundaries and evidence limits are explicit so IA evidence is not over-claimed as route guard, component, authorization, accessibility, or live user-research proof.

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `user-flow-modeling` for ordered task path behavior; `page-component-decomposition` for component-level layout; `design-system-rules` for visual styling and component library; `permission-boundary-modeling` for authorization model behind role-based navigation visibility.

# Completion Criteria

The capability is complete when **information is grouped, named, and navigable according to user tasks and user vocabulary** — with no database-noun navigation, no service-boundary leakage, designed empty states for every content area, explicit cross-module handoffs, and role-based visibility defined for every restricted navigation destination.
