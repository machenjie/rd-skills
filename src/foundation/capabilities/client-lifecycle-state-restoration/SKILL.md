---
name: client-lifecycle-state-restoration
description: "`analysis-agent`/`task-agent`/`review-agent`: use for installed-client lifecycle, termination, restoration, or identity-reset decisions; skip static UI and platform-API-only work."
---

# client-lifecycle-state-restoration

## Registry Trigger

**Use when**

- Client behavior must survive or intentionally reset across visibility changes, backgrounding, process termination, relaunch, crash, upgrade, logout, or account switch.

**Do not use when**

- No lifecycle or restoration decision.
- Only offline-sync policy.
- One platform API without a shared state rule.

## Skill Role

Define cross-client lifecycle states, snapshot authority, restoration eligibility, duplicate initialization, stale asynchronous completion, cancellation, and identity reset. A shared state rule means a shared cross-client restoration contract, not a platform callback. Exclude platform APIs, generic state-store selection, offline synchronization, packaging, and release workflow.

## High-Value Rules

- **Model lifecycle states by allowed effects.** Distinguish visible, obscured, background-capable, suspended, terminated, and relaunched states according to the repository's actual runtime contract.
- **Classify restorable state before serialization.** Preserve only user continuity that is safe to reconstruct while durable business truth remains with its authoritative owner.
- **Make initialization repeat-safe.** Give launch, activation, and restoration work explicit ownership so duplicate entry cannot register handlers or commit effects twice.
- **Bind snapshots to identity and compatibility.** Reject or migrate snapshots when account, session, schema, application version, or required source data no longer matches.
- **Require lifecycle generation for asynchronous completion.** Cancel disposable work and prevent stale results from mutating a newer screen, session, or account.
- **Restore intent without replaying effects.** Reconstruct navigation, drafts, and selections while reconciling consequential operations through their authoritative status.
- **Define reset behavior for destructive transitions.** Specify what survives crash or upgrade and what must clear on logout, account switch, corruption, or incompatible restoration.

## Anti-Patterns

- Treat an in-memory resume, process recreation, and cold launch as the same path.
- Restore captured credentials, permissions, server responses, or completed commands as current truth.
- Use one global startup flag while multiple scenes, windows, activations, or tests can initialize independently.

## Stop Conditions

Stop when snapshot ownership, restored identity, schema compatibility, or effect status is unknown. Escalate platform callback semantics to the applicable Domain Skill and route offline reconciliation to `offline-sync-conflict-resolution`.

## Output Contract

- lifecycle-restoration decision with state model snapshot contents and version initialization identity stale-work handling reset policy observable interruption evidence proof limits and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [restoration boundaries](references/restoration-boundaries.md) | targeted | Termination snapshot eligibility restoration compatibility or duplicate activation remains unresolved | Established repository state ownership already determines restoration and reset behavior | analysis-agent, task-agent, review-agent | selected-approach, proof-limit |
