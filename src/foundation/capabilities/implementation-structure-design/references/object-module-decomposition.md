# Internal Composition By Change Reason And Lifecycle

- Place code with the owner of its change reason, state, invariant, effect, protocol, lifecycle, and tests; compare co-location and private extraction before new structure.

These patterns compare co-location and extraction inside one established owner using change reason, state or resource lifecycle, contracts, dependency direction, reuse, tests, and fixtures.

## Co-Location And Extraction Evidence

| Signal | Co-locate | Separate or extract |
| --- | --- | --- |
| Change reason | The detail changes with one owner for the same accepted reason. | The responsibility has an independent accepted reason to change. |
| State or invariant lifecycle | The detail is private to the owner's state and invariant lifecycle. | It owns distinct state, invariant authority, transition rules, or cleanup. |
| Side effect or resource lifecycle | Ordering, failure, retry, and cleanup belong to the same coordinator. | Separation makes an independently owned effect, protocol, or resource lifecycle explicit. |
| Contract and visibility | No verified consumer needs a separate surface. | A current consumer, generated-source boundary, or compatibility contract requires distinct visibility. |
| Dependency direction | Co-location preserves inward dependencies and avoids a relay abstraction. | A separate boundary removes reach-through access and gives dependencies a clear direction without a cycle. |
| Reuse and consumer scope | Behavior belongs to one owner despite superficial duplication. | Current consumers share the same semantics, failure behavior, lifecycle, and accountable owner. |
| Tests and fixtures | Public behavior and fixtures are owned and understandable through the containing owner. | The extracted responsibility has a stable behavior boundary, fixture lifecycle, and clear next-change location. |

The "separate or extract" column authorizes owner-private new structure. If the decision adds an export, cross-owner/shared surface, package edge, cycle, or distributable contract, stop and route outward before placement.

## Placement Decision Record

- Record inspected owners and reuse candidates, selected and rejected locations, change reason, lifecycle, visibility, imports, and public surface.
- Record tests and fixtures before/after, generated-source authority and freshness handling, migration or rollback needs, and uninspected consumers.
- Add a validation plan with a positive owner-private case, a negative cross-owner/export case, and the consumer signal that would expose a wrong move.
- State proof limits and residual risk for dynamic imports, generated sources, hidden consumers, and intentional-copy drift.
- Route cross-module edges to `module-boundary-design` and unresolved model, effect, persistence, API, or behavior-preservation decisions to their owning Skills.
