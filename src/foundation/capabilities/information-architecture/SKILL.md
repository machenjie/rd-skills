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

# Non-Negotiable Rules

- **Organization is task-first, not noun-first.** Navigation menus that list database entities (Users, Orders, Products, Events) without task framing fail users who think in terms of goals (Manage team access, Track a delivery, Update pricing). Every navigation item must answer: "What does the user want to do from here?"
- **Separate user-facing concepts from storage models.** The fact that a "subscription" is stored as three tables (plans, subscriptions, billing_cycles) does not mean the navigation should have three entries. Merge, abstract, and rename to match user vocabulary.
- **Labels must match user vocabulary, not internal terminology.** Conduct a vocabulary audit: what does the user call this? "Ledger entries" → user says "Transactions." "Principals" → user says "Team members." Wrong labels increase task completion time and call center volume.
- **Navigation depth must not exceed 3 levels without search.** Beyond 3 levels of hierarchy, users lose orientation. Miller's Law (7±2 items per level) and progressive disclosure are the mitigations for breadth. Depth beyond 3 requires a search or filter mechanism.
- **Permission-aware visibility: show restricted items as locked, not invisible.** Completely hiding a navigation item for which the user lacks permission creates a "where did it go?" effect when permissions change. Recommended pattern: show item with a lock icon and tooltip explaining access requirement. Exception: items the user should not know exist (confidential feature, beta, regulatory restriction) may be fully hidden with clear documentation.
- **Every list, table, or card view must have a designed empty state.** An empty state without a call-to-action is a dead end. "No items found" is insufficient. Include: what goes here, why it is empty, what to do next (create first item, invite a team member, import data).
- **Cross-module handoff points must be explicit.** When a task spans two modules (e.g., Order → Customer; Invoice → Project), define the exact handoff: what link or action moves the user; what context is preserved (breadcrumb parent, back navigation); whether it is a deep link or a full navigation reset.

# Industry Benchmarks

Anchor against: **Jesse James Garrett "Elements of User Experience"** (2002) — IA exists at the structure layer between strategy/scope and skeleton/surface; separates conceptual structure (IA) from visual design. **Peter Morville & Louis Rosenfeld "Information Architecture for the World Wide Web"** (4th ed., O'Reilly) — Three circles: content, context, users; four core IA systems: organization, labeling, navigation, search. **Richard Saul Wurman LATCH principle** (1996) — five ways to organize information: Location, Alphabet, Time, Category, Hierarchy; choose organization scheme based on user task type. **Card Sorting** (Spencer, UXMethods; Optimal Workshop Optimal Sort) — open card sort validates user mental model before committing to IA; closed card sort tests proposed IA against user expectations; open sort for discovery, closed sort for validation. **Tree Testing** (Treejack; Nielsen Norman Group) — measures findability without visual design bias; target: > 70% directness score per primary task; measures whether users go directly to the right location without backtracking. **Jakob Nielsen "10 Usability Heuristics"** (1994) — Heuristic 1: Visibility of system status; Heuristic 6: Recognition over recall; Heuristic 8: Aesthetic and minimalist design — all inform IA decisions about what is visible and how much cognitive load navigation imposes. **WCAG 2.1 Success Criteria 2.4.1–2.4.8** — Navigation: bypass blocks (2.4.1); Page titled (2.4.2); Focus order (2.4.3); Link purpose (2.4.4); Multiple ways to find content (2.4.5); Headings and labels (2.4.6). **Mobile navigation patterns** — Apple HIG and Material Design 3 recommend bottom navigation for ≤ 5 primary items (thumb reach zone); top app bar for secondary navigation; drawer for infrequently used items. **WCAG 2.5.5** — Touch target size ≥ 44×44 CSS pixels for bottom navigation items. **Nielsen Norman Group "Information Scent"** (2003) — users scan page titles, link text, and headings for relevance cues; weak scent = abandonment at navigation node; test with click maps or first-click tests.

### Navigation Pattern Selection Matrix

| Pattern | Best for | Max items | Depth | Do not use when |
| --- | --- | --- | --- | --- |
| Top navigation bar | Global/primary sections (desktop) | 5-7 | 1-2 | Mobile primary nav (reach), > 10 items |
| Left sidebar | Section/product navigation | 7-15 | 2-3 | Mobile (collapses poorly), < 3 items |
| Bottom navigation | Mobile primary navigation | 3-5 | 1 | Desktop (not expected), > 5 items |
| Tabs | Peer-level sections within a page | 3-8 | 1 | Hierarchy (parent/child), > 8 tabs |
| Mega menu | Deep flat taxonomy (e-commerce catalog) | Unlimited | 2-3 | Small apps, B2B tools with < 10 sections |
| Breadcrumb | Hierarchical context / wayfinding | N/A | Any | Flat navigation (no hierarchy to show) |
| Progressive disclosure | Complex forms, step-by-step tasks | N/A | N/A | When all information is needed at once |

### IA Organization Scheme Selection

```
Given a user task type, select the organization scheme:

IF user_task = "find a specific known item" (e.g., find an order by ID)
  → Alphabetical or Search
  → Do not bury in category hierarchy

IF user_task = "browse and explore options" (e.g., product catalog)
  → Category hierarchy + faceted filter
  → Card sorting to validate category labels

IF user_task = "understand what happened over time" (e.g., activity log)
  → Time-based organization (reverse chronological default)
  → Date range filter required

IF user_task = "complete a multi-step workflow" (e.g., onboarding, checkout)
  → Task flow / wizard with progress indicator
  → Navigation back must be safe (no data loss)

IF user_task = "monitor and act on current state" (e.g., support queue, ops dashboard)
  → Status-based grouping (priority, urgency, type)
  → Filter + sort + bulk action pattern

IF user = "admin / operational user" (different mental model from end user)
  → Separate admin IA from product IA
  → Surfaced: audit trails, user impersonation, bulk operations, system health
```

# Selection Rules

Select this capability when **information grouping, navigation structure, labeling, and content discoverability** are the primary design concerns. Adjacent routing:

- Prefer `user-flow-modeling` when the primary concern is the ordered path through tasks and decision points.
- Prefer `page-component-decomposition` when the primary concern is component-level layout and implementation structure.
- Prefer `design-system-rules` when the primary concern is visual design tokens, component library, and styling.
- Prefer `permission-boundary-modeling` when the primary concern is who can see and do what, and the authorization model.
- Prefer `experience-impact-modeler` for end-to-end change impact review across user-facing surfaces.

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

# Failure Modes

- Navigation rebuilt from database entity names; user task completion rate on primary flows drops 25%; usability study required post-launch.
- Support portal restructured by service team boundaries; agents must open 3 tabs per ticket; handle time increases 40%; escalation to IA redesign.
- Deep link to a report page breaks when Reports section is permission-hidden; users click email notification and see 404; support spike.
- Empty dashboard for new users has no empty state CTA; 30% of new users churn before completing first action.
- Mobile navigation has 6 bottom items; thumb reach failure; right-side items inaccessible one-handed; WCAG 2.5.5 violation.
- Admin panel mirrors product navigation; "User impersonation" action buried 4 levels deep; support team spends 10 minutes locating per ticket.
- Cross-module handoff Order→Customer has no back-navigation context; user loses their order list position; returns to top of list every time.
- Labels from internal terminology ("Principals," "Artifacts," "Ledger") used in UI; users unfamiliar; task completion rate for new users = 60% vs 85% with user-tested labels.

# Output Contract

Return an information architecture plan with:

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
- `admin_ia` (if admin users exist: separate admin IA section or explicitly integrated)

# Quality Gate

The information architecture is complete only when:

1. Every navigation section is named in user task vocabulary (not internal noun or service name).
2. Cross-module task handoffs are mapped with explicit back-navigation behavior.
3. Role-based visibility defined for every section: visible / locked / hidden, with reasoning.
4. Empty states designed for every list, table, and card view with a CTA.
5. Navigation depth ≤ 3 levels, or search/filter provided as fallback.
6. Navigation pattern selected and justified per target device (mobile vs desktop).
7. Labels audited against user vocabulary (not internal terminology).
8. Deep link behavior defined for permission-restricted destinations (locked, not 404).
9. Admin IA addressed separately if operational user segment exists.
10. Validation method specified (card sort, tree test, or first-click test).

# Used By

- experience-impact-modeler
- frontend-change-builder

# Handoff

Hand off to `user-flow-modeling` for ordered task path behavior; `page-component-decomposition` for component-level layout; `design-system-rules` for visual styling and component library; `permission-boundary-modeling` for authorization model behind role-based navigation visibility.

# Completion Criteria

The capability is complete when **information is grouped, named, and navigable according to user tasks and user vocabulary** — with no database-noun navigation, no service-boundary leakage, designed empty states for every content area, explicit cross-module handoffs, and role-based visibility defined for every restricted navigation destination.
