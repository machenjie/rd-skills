# .NET Runtime, Deployment, And Interop Contracts

Use for runtime reachability, loading, ABI, UI-affinity, or deployment decisions.

## Decision Matrix

| Boundary | Evidence | Failure |
| --- | --- | --- |
| Trimming | Publish options; reflection/serialization/DI roots; annotations/descriptors; warning owner; plugins; smoke entry. | Suppressed warning or publish-only missing member. |
| Native AOT | Feature support; dynamic code/reflection; native dependencies; RID; diagnostics; size/startup goal; fallback. | Target behavior absent after successful compile. |
| Loading | Context owner; probes; shared contracts; versions; unload roots; concurrency; native resolution; trust. | Split type identity or callbacks/caches prevent unload. |
| P/Invoke | Header signature; convention; charset; layout; ownership; error; callback lifetime; architecture. | Truncation, leak, or corruption. |
| COM | Registration/activation; interface/version; apartment/pump; ownership/release; deployment. | Deadlock or wrong-owner release. |
| Desktop UI | Dispatcher/affinity; reentrancy; cancellation; result handoff; teardown. | Deadlock, off-owner access, or work outliving view. |
| Deployment | Framework; RID; host/runtime; dependent/self-contained; single-file/trim/AOT; native assets; update/rollback. | Wrong runtime, architecture, OS, or mode. |

## Required Proof

- Exercise publish mode/RID, dynamic reachability, and native dependencies.
- Prove loading identity, failure resolution, concurrent load, and unload after callback/cache release.
- Exercise invalid input, native failure, cancellation, wrong-thread access, and teardown on host.

## Primary Sources

[Native AOT](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/), [trimming](https://learn.microsoft.com/en-us/dotnet/core/deploying/trimming/fixing-warnings), [loading](https://learn.microsoft.com/en-us/dotnet/core/dependency-loading/understanding-assemblyloadcontext), [native interop](https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices), [unmanaged interop](https://learn.microsoft.com/en-us/dotnet/framework/interop/), [WPF](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/threading-model), [publish](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish), [RIDs](https://learn.microsoft.com/en-us/dotnet/core/rid-catalog). Accessed 2026-07-24.

## Proof Limits

Rolling sources require SDK/runtime, framework/UI, RID, OS/architecture, publish, native/COM evidence. Do not transfer `AssemblyLoadContext` to .NET Framework or WPF rules across UI frameworks. They do not prove reachability, ABI, apartment state, host availability, or performance.

## Required Record And Rejections

- Record target, loading owner, ABI/apartment/dispatcher, exercised artifact, limits, residual risk.
- Reject build or nullable/type syntax as runtime, immutability, loading, AOT, UI, or deployment proof.
