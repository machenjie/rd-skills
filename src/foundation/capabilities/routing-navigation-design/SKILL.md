---
name: routing-navigation-design
description: "`analysis-agent`/`task-agent`: use when routes, guards, redirects, deep links, breadcrumbs, back behavior, stale links, or recovery change; skip when navigation is unaffected."
---

# routing-navigation-design

## Registry Trigger

**Use when**

- design routes navigation guards deep links breadcrumbs and back behavior

**Do not use when**

- no task-local routing navigation design decision is required

## Skill Role

Define route identity, parameter and state semantics, navigation intent, guards, redirects, deep-link recovery, history behavior, and route-level evidence. Exclude authorization and page interaction design.

## High-Value Rules

- **Treat route identity as a consumer contract.** Define canonical path, parameters, query state, fragments, aliases, serialization, and compatibility for bookmarks, shared links, analytics, crawlers, and external launchers relevant to the task.
- **Separate reachability from permission.** Route guards may coordinate navigation, but protected actions and resources remain enforced at their authoritative service or policy boundary; avoid leaking existence through divergent route behavior.
- **Preserve navigation intent through authentication and recovery.** Validate return targets, tenant and account context, stale state, and open-redirect boundaries before resuming an interrupted path.
- **Make redirects deliberate and bounded.** State source, destination, parameter preservation, loop prevention, history replacement or addition, compatibility window, and fallback when the destination is unavailable.
- **Model history and back behavior by user task.** Cover entry from internal navigation, direct link, refresh, external launcher, modal or nested flow, completion, cancellation, and expired state without assuming one stack shape.
- **Give asynchronous destinations honest states.** Distinguish resolving, denied, missing, stale, failed, redirected, pending, and completed outcomes; preserve uncertainty for operations whose server result is not known.
- **Prove canonicalization and recovery paths.** Exercise affected aliases, malformed and encoded parameters, tenant changes, deep links, refreshes, redirect chains, and back transitions with current router and platform evidence.

## Anti-Patterns

- Use a client guard as the authorization boundary or expose resource existence through route-specific denial behavior.
- Redirect broadly while dropping intent, query state, tenant context, or recovery information, or create loops between guards.
- Treat internal click navigation as proof for direct links, refresh, stale bookmarks, external launchers, and browser history.

## Stop Conditions

Escalate when canonical route ownership is unknown, return targets or deep links cross trust boundaries, or compatibility consumers are uninspected. Also escalate when history can repeat consequential actions, routing leaks authorization, or the current environment cannot exercise affected recovery paths.

## Output Contract

- routing and navigation decision with canonical identity, state and parameter contract, guard and redirect semantics, intent recovery, history behavior, compatibility evidence, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | URL redirect history or compatibility behavior has competing choices | established route contract determines direct-entry and navigation behavior | task-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | route changes guards redirects deep links parameters or recovery states | no route guard URL or navigation behavior changes | task-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | guard redirect deep-link or public-link claims need fresh proof | current route tests and consumer inventory prove each claim | task-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
