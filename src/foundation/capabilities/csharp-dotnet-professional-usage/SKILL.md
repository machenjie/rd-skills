---
name: csharp-dotnet-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for C# async, resource, type, DI, trimming/AOT, loading, interop, UI, or deployment decisions."
---

# csharp-dotnet-professional-usage

## Registry Trigger

**Use when**

- C# or .NET source changes async, resource, type, DI, runtime, interop, UI, publish, or deployment behavior.

**Do not use when**

- C# is incidental, or only Windows identity, signing, manifest, capability, or packaging metadata changes.

## Skill Role

Own C#/.NET language and runtime semantics; exclude Windows policy and generic concerns.

## High-Value Rules

- Select `async-resource-and-iterator-contracts` for active async, cancellation, resource, iterator/LINQ, null/type, or DI decisions.
- Select `runtime-deployment-and-interop-contracts` for active trim/AOT, loading, native/COM, UI, RID, publish, or deployment decisions.
- Bind decisions to current compiler, runtime, target, host, caller, and owner evidence.

## Anti-Patterns

- Compilation substituted for runtime, ownership, ABI, or deployment evidence.

## Stop Conditions

- Stop on unknown controlling version or boundary.
- Route Windows policy and generic risks to their owners.

## Output Contract

- C#/.NET decision with caller and owner paths async cancellation resources type enumeration DI runtime publish interop UI invalid teardown outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [async resource and iterator contracts](references/async-resource-and-iterator-contracts.md) | targeted | Async/cancellation disposal iterator/LINQ nullable value/reference or DI lifetime changes | These language execution and ownership boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [runtime deployment and interop contracts](references/runtime-deployment-and-interop-contracts.md) | targeted | Trimming/AOT assembly loading native/COM interop UI dispatch target RID or publish mode changes | Runtime reachability loading ABI affinity and deployment remain unchanged | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
