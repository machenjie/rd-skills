---
name: state-management-design
description: "`task-agent`: use when local, server, global, derived, optimistic, persisted, form, auth, or cache state ownership changes; skip when state boundaries are unaffected."
---

# state-management-design

## Registry Trigger

**Use when**

- choose local server global derived optimistic and persisted state boundaries

**Do not use when**

- no task-local state management design decision is required

## Skill Role

Define state classification, authority, identity, ownership scope, derivation, synchronization, optimistic and persisted behavior, cleanup, and frontend evidence. Exclude backend lifecycle, cache architecture, and permission policy.

## High-Value Rules

- **Classify state by authority and lifetime.** Distinguish local interaction, form draft, server-owned, cached, derived, navigation, authentication context, optimistic, and persisted state before choosing storage or sharing scope.
- **Keep one authoritative owner per state meaning.** Store durable business truth at its server or domain owner, derive redundant views where feasible, and define synchronization when copies are unavoidable.
- **Scope state to the narrowest consumer set.** Use component, feature, route, request, session, account, tenant, or application scope according to actual coordination and cleanup needs, not convenience.
- **Bind identity and freshness.** Include user, tenant, resource, query, version, and relevant policy context in keys and invalidation so account switching or late responses cannot cross boundaries.
- **Coordinate async and optimistic transitions.** Define operation identity, supersession, cancellation, stale arrival, server rejection, conflict, rollback or reconciliation, and forbidden duplicate effects.
- **Treat persistence as a privacy and compatibility boundary.** Apply current classification, expiry, encryption, clear-on-logout or account change, migration, corruption, and backup behavior before storing sensitive or long-lived client state.
- **Prove ownership and cleanup paths.** Exercise navigation, refresh, account switch, concurrent requests, failure, recovery, and unmount or shutdown behavior with explicit limits on uninspected surfaces.

## Anti-Patterns

- Promote state globally because prop flow is inconvenient, or duplicate server state without an invalidation owner.
- Key cache or persisted state without tenant, account, resource, or query identity needed to prevent cross-context reuse.
- Let a stale response, optimistic failure, logout, or navigation leave durable or sensitive state under the wrong owner.

## Stop Conditions

Escalate when state authority is ambiguous, copies cannot be reconciled, identity can cross users or tenants, or optimistic effects are consequential and irreversible. Also escalate when persisted state lacks privacy or migration ownership, or cleanup cannot be verified across lifecycle boundaries.

## Output Contract

- state-management decision with classification, authority and scope, identity and freshness, async and optimistic behavior, persistence policy, cleanup evidence, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | state ownership storage freshness invalidation or persistence choices remain unresolved | one authoritative owner determines storage lifecycle and reset behavior | task-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects server UI form auth derived or persisted state | local state edit preserves ownership lifetime and synchronization | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | invalidation logout rollback or persistence claims need fresh proof | current stores hooks fixtures and tests prove each claim | task-agent | evidence-record, proof-limit, residual-risk |
