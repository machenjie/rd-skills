# Layered Architecture Evidence Patterns

Use this reference when closure depends on proving dependency direction, business-rule placement, layer exceptions, import-graph freshness, architecture checks, or graph/memory claims. Keep the main capability body for routing and output shape; load this file only for concrete evidence mapping.

## Claim To Evidence Map

| Claim | Strong evidence | Weak or invalid evidence | Residual risk if absent |
| --- | --- | --- | --- |
| Controllers contain no business decisions | Current entry-point source plus use-case/domain tests for the moved rule | Folder naming or "thin controller" statement | Delivery mechanisms diverge and duplicate policy |
| Domain has no infrastructure imports | Fresh import graph, architecture rule output, or source scan for domain package | Prior graph, package layout only, or memory claim | Domain becomes untestable without DB/framework/queue |
| Application owns transaction boundary | Use-case source, unit-of-work owner, rollback rule, repository participant list | Repository method naming only | Partial commits or hidden cross-aggregate transaction drift |
| Infrastructure exceptions are translated | Adapter source and negative test/review mapping provider error to domain/application error | Catch-all wrapper with no provider case | Provider/DB/framework types leak inward or outward |
| Layer exception is bounded | Exception ledger with owner, reason, expiry/review trigger, containment test, and migration trigger | "Temporary" comment or undocumented local convention | Architecture debt becomes normalized |
| Architecture check is enforceable | CI command, tool config, exit code, report path, changed import scope, and freshness | Manual review only or stale check before package move | Dependency direction erodes silently |
| Graph/memory layering claim is current | Direct source paths confirm graph or memory claim after final edit | Compaction summary or prior report alone | Closure accepts stale architecture shape |

## Changed Layer To Validation Map

For each changed entry point, use case, domain rule, repository interface, adapter, transaction boundary, exception mapping, dependency rule, architecture exception, and enforcement check, record:

```yaml
layer_validation_map:
  changed_surface: ""
  layer: presentation | application | domain | infrastructure | cross_layer
  decision: ""
  source_paths: []
  validation:
    command: ""
    exit_code: null
    artifact_or_log: ""
    proves: ""
    does_not_prove: ""
  exception:
    owner: ""
    expiry_or_review_trigger: ""
    containment_test: ""
  residual_risk:
    owner: ""
    reason: ""
```

## Closure Checks

- Reject closure when domain import claims rely on folder names, stale graph, or memory without current source/import evidence.
- Reject closure when a deliberate layer exception lacks owner, review trigger, containment test, and residual-risk owner.
- Downgrade architecture check evidence if it ran before the final import/package/source edit.
- Do not treat a layer map as proof of domain invariant correctness, persistence behavior, distributed transaction safety, or release readiness.
