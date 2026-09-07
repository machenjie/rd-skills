---
name: client-lifecycle-state-restoration
description: "Use for installed-client lifecycle/restoration; skip static, offline-only, and platform-API-only work."
---

# client-lifecycle-state-restoration

## Registry Trigger

**Use when**

- A lifecycle or restoration decision is active.

**Do not use when**

- Skip absent lifecycle/restoration, offline-only policy, or a platform API without a shared state rule.

## Skill Role

Own shared lifecycle and restoration boundaries; exclude platform callbacks, stores, offline sync, packaging, and release.

## High-Value Rules

- **Classify restoration.** Define lifecycle effects and snapshot authority.
- **Fence restored work.** Bind state and completion to identity and compatibility.
- **Reconcile interruption.** Restore intent without replaying effects; define reset transitions.

## Anti-Patterns

- Local success is not lifecycle-restoration contract proof.

## Stop Conditions

Stop on unknown snapshot authority, identity, compatibility, or effect status.

## Output Contract

- lifecycle-restoration decision with state model snapshot contents and version initialization identity stale-work handling reset policy observable interruption evidence proof limits and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [restoration boundaries](references/restoration-boundaries.md) | targeted | Termination snapshot eligibility restoration compatibility or duplicate activation remains unresolved | Established repository state ownership already determines restoration and reset behavior | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
