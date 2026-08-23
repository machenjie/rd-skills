---
name: infrastructure-as-code-safety
description: "IaC state, identity, drift, destruction, and recovery safety."
---

# infrastructure-as-code-safety

## Registry Trigger

**Use when**

- IaC state/identity/drift/destruction/recovery/proposal limits

**Do not use when**

- docs, production mutation, or provider-only policy

## Skill Role

Own cross-tool state/identity/destruction/recovery; exclude adjacent and production authority.

## High-Value Rules

- Bind state authority and layer boundaries.
- Bind proposals to source/recorded/effective state, identity/effects/recovery, versions, and unknowns.
- Reject unproved tool equivalence, execution, or convergence.

## Anti-Patterns

- Local success is not IaC evidence.

## Stop Conditions

- Stop on unresolved authority, effects, recovery, or production mutation.

## Output Contract

- target and state authority proposal limits identity and graph effects destruction sensitive outcomes recovery validation proof limits and residual owner

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [state plan and drift contracts](references/state-plan-and-drift-contracts.md) | targeted | State authority locking drift unknown values or proposal freshness differs by the selected tool | One bounded source change preserves recorded and effective state without tool-specific proposal interpretation | analysis-agent, task-agent, review-agent | decision-record, proof-limit, residual-risk |
| [identity destruction and recovery contracts](references/identity-destruction-and-recovery-contracts.md) | targeted | Resource identity targeting replacement destruction protection recovery or secret exposure differs by the selected tool | No identity destructive sensitive or recovery outcome can change | analysis-agent, task-agent, review-agent | decision-record, proof-limit, residual-risk |
