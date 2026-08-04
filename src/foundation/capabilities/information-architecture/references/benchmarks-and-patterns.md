# Information Architecture Decision Traps

This reference isolates information-architecture decisions about task grouping, labels, canonical ownership, findability, visibility, and lifecycle handoffs.

## Decision Matrix

| IA facet | Facts to establish | Accident signal |
| --- | --- | --- |
| Task grouping | Named actor, task or decision, vocabulary, frequency, consequence, and current entry context | A service, team, table, or internal taxonomy becomes the user hierarchy without task evidence |
| Labels and concepts | Scope, owner, role meaning, lifecycle, locale, ambiguity, and source vocabulary | The same label names different objects or states across surfaces |
| Canonical ownership | Source of truth, projections, edit authority, freshness, archive, deletion, and stale-copy behavior | Copies diverge or a projection becomes editable without a reconciliation owner |
| Findability | Search, browse, navigation, direct entry, assisted discovery, known context, and recovery path | One discovery mode strands actors who enter with different knowledge or permissions |
| Visibility presentation | Current role evidence, visible, locked, hidden, contextual rules, disclosure, and next action | Presentation leaks existence or is mistaken for backend authority |
| Cross-module handoff | Destination meaning, required context, direct-entry behavior, return path, and lifecycle transition | A link lands successfully but loses actor intent, context, or recovery |
| Structural states | Empty, unavailable, archived, stale, partial, permission-limited meaning and next action | A generic state list creates distinctions with no changed meaning or action |

## Decision Limits

- Current actor, vocabulary, ownership, role, lifecycle, and discovery evidence selects the structure; a named pattern does not settle it.
- Navigation and search observations cover the measured channel, cohort, event definition, and time window; unobserved entry paths remain unknown.
- Hidden or locked presentation does not establish authorization, confidentiality, or data filtering.
- A prototype or review can expose label and hierarchy risk without proving production findability or accessibility.
- Route and history mechanics, detailed interaction states, component governance, and executable validation remain with their specialist owners.
- Final claims cite current source and scoped post-change evidence; otherwise record `not_run` and the remaining information-architecture risk.
