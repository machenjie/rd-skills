# Permission Boundary Evidence Patterns

Load this reference when permission authority, enforcement reachability, object or tenant scope, collection or bulk behavior, denial, delegation, rollout, or negative-path claims need fresh proof. Do not use it as a second permission tutorial.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Decision inputs are authoritative | Current subject/resource/relationship/policy sources, caller-controlled fields, evaluation path, and conflicting or unavailable-state behavior | Does not prove reachability from uninspected entry points |
| Object or tenant scope is enforced | Protected path, authoritative identity and resource scope, policy or query point, plus wrong-owner and wrong-tenant cases | Does not cover sibling routes, jobs, reports, caches, or deployed grants |
| Enforcement precedes disclosure or effect | Route-to-decision-to-query/effect trace for API, RPC, worker, consumer, admin, or support paths in scope | Does not prove unknown entry points or external consumers |
| Collection and bulk semantics preserve scope | Predicate or aggregate decision, pagination/count/cache/export behavior, mixed-scope fixture, partial or atomic result, and continuation behavior | Does not cover uninspected derived views, very large runs, or disaster replay |
| Denial follows the current disclosure contract | Contract and implementation path, client-safe body or signal, stable internal reason, audit sample, and invisible/visible cases selected from actual semantics | Does not prove gateway, localization, SDK, or client transformations unless inspected |
| Delegated entitlement is bounded | Resource/action/tenant/run or purpose scope, delegation source, real/effective actor, end condition, audit sample, and misuse case | Does not prove credential lifecycle, human-process compliance, or unrelated tools |
| Policy change preserves intended behavior | Old/new allow-deny cases, policy or relationship version, partial-rollout and stale-state behavior, rollback path, and final-edit validation | Does not prove production policy data or propagation timing |

## Freshness And Closure

- Treat prior matrices, reviews, generated contracts, audit notes, and compaction summaries as search leads until current routes, services, repositories, policies, jobs, support tools, tests, owner, and scope match.
- Classify known and discovered protected paths as inspected, not applicable, or unknown; keep unknown and externally owned paths as residual scope.
- Re-run selected positive and negative cases after the final route, query, policy, relationship, generated artifact, fixture, or audit change.
- Map the final confidence claim to current source paths, fixtures, parsed validation outcomes, audit evidence, owner evidence, and explicit unverified scope.
