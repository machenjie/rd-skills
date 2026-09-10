# Component Placement and Reuse Gates

Use this Reference only for the named component-placement-and-reuse-gates decision.

## Decision Rules

Placement evidence covers the existing owner, reuse scan, consumer list, public/private boundary, and test placement.

- Choose feature-local, design-system, shared UI, route-level, or generated placement from that evidence.
- Stop a new shared component, hook, global store, wrapper API client, mode flag, or dependency until current consumers, native or design-system alternatives, and a rollback or deletion path are proven.
- Require current variation, multiple implementations, a real boundary, or established architecture to justify a shared abstraction; consumer count alone is not decisive. Keep domain assumptions within their owner.
- Do not create shared UI or a hook merely because feature-local code feels repetitive.

Return the placement boundary, selected approach, rejected reuse candidates, affected consumers, and residual risk.
