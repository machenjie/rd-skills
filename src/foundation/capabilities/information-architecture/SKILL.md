---
name: information-architecture
description: "`analysis-agent`/`task-agent`: use when hierarchy, labels, findability, ownership, visibility, lifecycle, or cross-module discovery changes; skip route/state-only work."
---

# information-architecture

## Registry Trigger

**Use when**

- User-facing information hierarchy, grouping, labels, findability, canonical ownership, visibility, lifecycle, or cross-module discovery changes.
- Actors must locate, interpret, enter, revisit, or leave information across navigation, search, browse, direct entry, or operational handoffs.

**Do not use when**

- The open decision is an ordered journey, route mechanics, interaction-state detail, component layout, or visual styling.
- No user-facing hierarchy, label, ownership, visibility, lifecycle, or findability decision changes.

## Skill Role

Define task grouping, labels, canonical content ownership, findability, visibility presentation, lifecycle placement, and cross-module discovery. Exclude actor discovery, journey order, routing, authorization, and interaction-state detail.

## High-Value Rules

- Derive grouping from a named actor's task, decision, and vocabulary; database tables, service boundaries, and organization charts are evidence, not the default user hierarchy.
- A label states scope, owner, lifecycle, role meaning, and locale-sensitive ambiguity where those facts can change interpretation; internal terms do not become user language by repetition.
- Name the canonical source, projections, edit authority, freshness signal, archive or deletion behavior, and stale-copy treatment before the same information appears in multiple surfaces.
- Choose search, browse, navigation, direct entry, or assisted discovery from the actor's known context and task; a single discovery mode is not assumed to serve every entry condition.
- Distinguish visible, locked, hidden, and contextual presentation only when current product and policy evidence supports the distinction; information architecture does not grant authority.
- For cross-module and deep-link entry, preserve destination meaning, required context, return path, and lifecycle behavior while leaving mechanics with the routing owner.
- Represent reachable empty, unavailable, archived, stale, partial, or permission-limited structures only when their meaning or next action differs; do not expand a generic state catalog.

## Anti-Patterns

- The navigation tree mirrors database or service structure while actor tasks and vocabulary remain unexamined.
- Content is copied across surfaces without a canonical owner, freshness contract, or archive and deletion behavior.
- Hidden or locked presentation is used as an authorization rule or selected by convention without current role evidence.
- One role, locale, channel, or observed discovery path is generalized to every actor and entry condition.

## Stop Conditions

- Route actor, journey, interaction, navigation, authorization, component, design-system, implementation, acceptance, and executable-proof decisions to their named owners.

## Output Contract

- information-architecture decision with task grouping, labels, canonical ownership, findability, visibility, lifecycle, handoffs, current evidence, proof limits, residual risk, and specialist routes

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Competing task group label ownership visibility findability lifecycle or handoff choices can change the information structure | Current information owners labels visibility rules and discovery paths settle the affected structure | analysis-agent, task-agent | option-comparison, selected-approach |
