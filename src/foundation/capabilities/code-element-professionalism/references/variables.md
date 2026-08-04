# Variable State And Lifetime

This guide resolves local variable hazards that can change authority, state meaning, resource ownership, transaction behavior, or isolation.

## Variable Contract

| Variable hazard | Decision to expose | Accident signature |
| --- | --- | --- |
| First valid value | Place the first assignment where the value becomes valid; an earlier declaration identifies the language or API constraint and the reachable assignment paths | Error, loop, retry, cancel, logging, cleanup, or response reads an unset placeholder |
| State or sentinel | Distinguish absent, empty, false, zero, unknown, denied, expired, partial, error, and not-loaded when their behavior differs | A convenient default silently represents several domain states |
| Scope or shadowing | Keep a readable lifetime and reader set; retained shadowing stays visibly separate from material error, tenant, permission, transaction, resource, context, or cursor values | A later commit, close, return, or log observes the wrong binding |
| Mutation or concept identity | Give mutable state one owner and one semantic concept through time | An identifier becomes an object, response, or error, or several callbacks mutate it without ownership |
| Capture, alias, or lifetime | Identify capture time and mode, alias mutability, and whether a handle or value outlives the local scope | Late loop capture, stale request context, race, use-after-close, or caller mutation leaks through an alias |
| Global or module state | Identify construction, synchronization, reset, shutdown, reload/retry behavior, and test/request/user/tenant isolation | Mutable defaults, caches, registries, secrets, or context leak across identities or runs |

## Proof And Routing

Exercise applicable sentinel classes, assignment branches, capture schedules, alias mutation, reset, and isolation. Type and static checks leave domain equivalence, runtime alias ownership, and unexercised schedules outside their proof.
Route signature or placement to `implementation-structure-design`, language ownership and capture rules to `language-idiom-enforcement`, races to `concurrency-control`, and lifecycle leaks to `reliability-observability-gate`.
