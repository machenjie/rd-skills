# Component Placement and Reuse Gates

Use this Reference only for the named component-placement-and-reuse-gates decision.

## Decision Rules

Placement evidence covers the existing owner, reuse scan, consumer list, public/private boundary, and test placement.

- Choose feature-local, design-system, shared UI, route-level, or generated placement from that evidence.
- Stop a new shared component, hook, global store, wrapper API client, mode flag, or dependency until current consumers, native or design-system alternatives, and a rollback or deletion path are proven.
- Reject a shared abstraction with one consumer or hidden domain assumptions.
- Do not create shared UI or a hook merely because feature-local code feels repetitive.

Return the placement boundary, selected approach, rejected reuse candidates, affected consumers, and residual risk.
