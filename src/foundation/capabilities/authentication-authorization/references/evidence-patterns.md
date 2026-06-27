# Authentication Authorization Evidence Patterns

Load this reference only when authorization proof depends on repository graph reachability, project memory, execution trajectory, validation freshness, generated contracts, or operation-to-validation mapping. Do not load it for quick routing or metadata-only edits.

## Evidence Surfaces

| Surface | Accept as evidence when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current routes, resolvers, workers, consumers, repositories, policies, support/admin tools, exports, caches, generated contracts, and tests are inspected for the protected operation. | A graph summary claims coverage without source paths, owners, generated-contract impact, or bypass-capable entry points. |
| Project memory | Prior policy decisions, tenant rules, audit exceptions, incidents, and support-flow constraints have date, owner, scope, and unchanged paths. | Memory predates new endpoints, jobs, support tools, roles, token claims, tenant rules, or policy files. |
| Execution trajectory | Permission tests, same-pattern scans, audit samples, failed probes, and repair steps ran after the final policy/edit path. | Evidence covers only the happy path, predates the final edit, or hides failed enforcement probes. |
| Validation broker | Changed protected operations map to narrow/module/full validators with parsed outcome, exit code, and freshness. | Validation is partial, stale, lacks exit code, or proves only authentication rather than authorization. |
| Audit and telemetry | Allow/deny events have safe fields, stable reason codes, policy version, correlation id, and owner-approved retention. | Logs include sensitive values, unbounded labels, ambiguous actors, or no reason code/policy version. |

## Graph Coupling

Authorization graph evidence must include every path that can reach protected data or actions:

- entry points: HTTP routes, GraphQL resolvers, RPC handlers, CLIs, admin/support tools, scheduled jobs, message consumers, webhooks, imports, exports, and bulk actions;
- data access: repository methods, query builders, DB row-level security policies, search indexes, caches, materialized views, object storage, report builders, and generated clients;
- policy surfaces: PDP/policy files, PEP adapters, role/scope grants, relationship tuples, service-account scopes, support override rules, and audit writers;
- bypass candidates: direct SQL/admin consoles, maintenance scripts, background workers, cache warmers, data exports, and downstream integrations.

Mark each path as inspected, not applicable, or unknown. Unknown protected paths block approval for high-risk authz changes or become named residual risk with an owner.

## Memory Freshness

Project memory and old policy matrices are hints only:

- Accept memory when date, scope, owner, tenant model, role model, policy version, and affected paths still match current source.
- Reject or downgrade memory when new routes, jobs, support flows, generated clients, tenant rules, policy files, cache layers, or service accounts changed since the record.
- Preserve accepted memory in `graph_memory_execution_validation`; preserve rejected memory in `evidence_limits` with the stale assumption named.
- Never let memory replace current source inspection for protected operations.

## Authorization-To-Validation Map

Use this compact map inside `changed_authz_to_validation_map`:

| Protected operation element | Required proof | Freshness rule | Closure consequence |
| --- | --- | --- | --- |
| Subject identity | Server-derived session/token/service account source, not caller-controlled id. | Fresh after auth middleware or service credential change. | Block if subject source is ambiguous. |
| Object rule | Subject-action-resource-tenant relationship and PDP rule. | Fresh after role, relationship, tenant, ownership, or policy edit. | Block if role-only rule protects object operation. |
| Enforcement point | PEP at controller/resolver/service/repository/worker plus query-time tenant/owner predicate where needed. | Fresh after route, query, worker, resolver, or repository change. | Block if only frontend/gateway enforces. |
| Denial behavior | 401/403/404 taxonomy, safe message, audit reason code, and existence-leak decision. | Fresh after API/error contract change. | Conditional approval only with owner. |
| Audit event | Allow/deny event with actor, effective subject, resource, tenant, action, policy version, correlation id, and purpose when required. | Fresh after audit schema/logging change. | High-risk actions cannot close without audit. |
| Cache/claim invalidation | TTL, invalidation trigger, stale-claim denial, and policy update behavior. | Fresh after token/session/cache/policy change. | Residual risk requires expiry and owner. |
| Validation | Positive plus unauthenticated, insufficient-scope, wrong-tenant, wrong-owner, stale-claim, mass-assignment, list/export, and service-account cases as applicable. | Re-run after final source, policy, fixture, generated client, or config edit. | Do not report partial tests as full authz proof. |

## Efficiency Guardrail

Keep the main `SKILL.md` focused on routing, rules, output contract, and quality gate. Put detailed graph-memory-execution evidence patterns here, and load this file only when the authorization answer would otherwise over-claim current-source coverage, memory freshness, or validation proof.
