# Service Orchestration Evidence Patterns

These evidence patterns bound claims about application orchestration ownership, authorization order, rule delegation, commit handoff, external-effect recovery, and failure translation.

## Orchestration Claim Map

| Orchestration claim | Current path evidence | Unproved boundary |
| --- | --- | --- |
| One use case owns the sequence | current callers, actor/intent, public operations, transaction/effect map, and rejected placements | uninspected entry points can introduce another authority |
| Authorization precedes protected access | policy or scoped-query path plus denied-case evidence that records repository call order | timing channels and uninspected support paths remain outside the claim |
| Domain authority owns the rule | service branch review, domain operation, denied case, and duplicate-rule scan | future callers or unsearched writers can bypass the route |
| Commit and handoff are coordinated | transaction owner, participating writes, durable event/work record, rollback or crash-path evidence | local proof does not establish production contention or provider behavior |
| External effect has recovery semantics | call site, operation identity, timeout/cancellation, unknown-outcome path, and compensation or reconciliation evidence | provider partitions and broader traffic remain unproved unless exercised |
| Failure mapping preserves meaning | dependency failure fixtures and stable use-case results for denied, partial, duplicate, cancellation, and terminal cases | transport and consumer mappings need their own contract evidence |

## Freshness And Limits

- Refresh evidence after changes to callers, authorization, service ports, transaction owner, domain operations, repositories, events, provider adapters, retry policy, or tests.
- Keep first-failure evidence separate from later retry, compensation, or reconciliation success.
- Distinguish source review, local fixture, equivalent store/provider, staged behavior, and live authority.
- Close with uninspected entry points, runtime/provider/scale limits, residual owner, and routed follow-up.
