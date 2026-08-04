---
name: csharp-dotnet-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use for C# async, resource, type, DI, trimming/AOT, loading, interop, UI, or deployment decisions."
---

# csharp-dotnet-professional-usage

## Registry Trigger

**Use when**

- C# or .NET code changes async/cancellation, disposal, iterators/LINQ, nullable contracts, value/reference behavior, DI lifetime, trimming/AOT, assembly loading, native/COM interop, UI dispatch, or deployment.
- A compiler, target framework, RID, host, framework, or generated boundary can change behavior beyond compilation.

**Do not use when**

- C# appears only in comments/generated output, or another-language change has no C#/.NET source.
- The change is only MSIX identity, signing, manifest capability, packaging metadata, or Windows policy with no C#/.NET semantic decision.

## Skill Role

Own C# language and .NET runtime/library semantics. Leave Windows identity/policy and generic concerns to their owners.

## High-Value Rules

- Preserve async ownership, `CancellationToken` propagation, context/dispatcher needs, observed exceptions, and caller-visible cancellation.
- Define one owner and ordered cleanup for each disposable resource, including partial construction, repeated disposal, and cleanup failure.
- Define iterator and LINQ execution plans by enumeration count, deferred effects, provider translation, cancellation, and resource lifetime.
- Validate nullable compiler contracts across reflection, serialization, interop, generated, and disabled-context runtime boundaries.
- Choose class, struct, record, or `ValueTask` from identity, copy, equality, boxing, consumption, and compatibility evidence.
- Enforce DI lifetime ownership against shorter-lived capture, service location, and disposal of container-owned instances.
- Prove trim/AOT reachability for reflection, serialization, DI, dynamic code, and plugins in the actual publish mode.
- Define load context, native/COM ABI and apartment, UI dispatcher, target, RID, and framework-dependent/self-contained deployment.

## Anti-Patterns

- `async void`, fire-and-forget tasks, or sync-over-async hides failure, cancellation, context deadlock, or owner teardown.
- A `using`, finalizer, DI container, GC, or `await using` is assumed to establish the required cleanup order without failure-path proof.
- Nullable-clean compilation, a record, or a struct is treated as runtime null safety, deep immutability, or cheap copying.
- Build success is treated as reflection, native loading, trimming, AOT, UI-affinity, or deployment proof.

## Stop Conditions

- Stop until behavior-controlling compiler, target, runtime, RID, publish, host, and desktop versions are known.
- Route Windows identity, registry deployment, entitlements/capabilities, signing, installer, and OS policy to the Windows domain owner.
- Route concurrency, security, persistence, API compatibility, performance, and testing to their owners.
- Stop on an unknown resource owner, enumeration site, DI scope, reflection root, native ABI, COM apartment, UI dispatcher, or deployment target.

## Output Contract

- C#/.NET decision with caller and owner paths async cancellation resources type enumeration DI runtime publish interop UI invalid teardown outcomes evidence limits and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [async resource and iterator contracts](references/async-resource-and-iterator-contracts.md) | targeted | Async/cancellation disposal iterator/LINQ nullable value/reference or DI lifetime changes | These language execution and ownership boundaries remain unchanged | task-agent, review-agent, analysis-agent | decision-record, residual-risk |
| [runtime deployment and interop contracts](references/runtime-deployment-and-interop-contracts.md) | targeted | Trimming/AOT assembly loading native/COM interop UI dispatch target RID or publish mode changes | Runtime reachability loading ABI affinity and deployment remain unchanged | task-agent, review-agent, analysis-agent | selected-approach, proof-limit, residual-risk |
