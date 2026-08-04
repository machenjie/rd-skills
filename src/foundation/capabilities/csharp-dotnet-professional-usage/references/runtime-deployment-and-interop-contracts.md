# .NET Runtime, Deployment, And Interop Contracts

Use this reference to compare runtime reachability, loading, ABI, UI-affinity, and deployment choices.

## Decision Matrix

| Boundary | Required evidence | Failure signal |
| --- | --- | --- |
| Trimming | Actual publish options, reflection/serialization/DI roots, annotations or descriptors, warning ownership, plugin policy, and smoke entry points | Warnings are suppressed or a dynamically reached member disappears only after publish |
| Native AOT | Supported runtime features, dynamic-code/reflection use, native dependencies, target RID, diagnostics, size/startup goal, and fallback | Compilation succeeds but dynamic loading, runtime generation, or target-native behavior is unavailable |
| Assembly loading | Load-context owner, probing paths, shared contracts, version rules, unload roots, concurrency, native dependency resolution, and trust | Equal-named types come from different contexts or callbacks/caches prevent unload |
| P/Invoke | Header-derived signature, calling convention, charset/string marshalling, struct layout, ownership, error retrieval, callback lifetime, and architecture | A default marshalling assumption truncates data, leaks a handle, or corrupts layout |
| COM | Registration/activation model, interface/version, apartment, message pump, marshalled ownership, release owner, and deployment | A thread/apartment transition deadlocks or final release occurs on the wrong owner |
| Desktop UI | Framework-specific dispatcher, thread affinity, reentrancy, cancellation, background result handoff, and teardown | Sync wait deadlocks, background code touches UI state, or dispatcher work outlives the view |
| Deployment | Target framework, RID, host/runtime availability, framework-dependent or self-contained mode, single-file/trim/AOT options, native assets, and update/rollback | The artifact is built for a different runtime, architecture, OS, or publish mode |

## Required Proof

- Build and exercise the exact publish mode and target RID, including a dynamically reached entry point and native dependency when present.
- For custom loading, prove shared-contract identity, failure resolution, concurrent load behavior, and unload after callbacks/caches are released.
- For native/COM/UI boundaries, exercise invalid input, native failure, cancellation, wrong-thread access, and teardown on the target architecture/host.

## Primary Sources

- [Native AOT deployment](https://learn.microsoft.com/en-us/dotnet/core/deploying/native-aot/)
- [Fix trimming warnings](https://learn.microsoft.com/en-us/dotnet/core/deploying/trimming/fixing-warnings)
- [AssemblyLoadContext concepts](https://learn.microsoft.com/en-us/dotnet/core/dependency-loading/understanding-assemblyloadcontext)
- [Native interoperability best practices](https://learn.microsoft.com/en-us/dotnet/standard/native-interop/best-practices)
- [Interoperate with unmanaged code](https://learn.microsoft.com/en-us/dotnet/framework/interop/)
- [WPF threading model](https://learn.microsoft.com/en-us/dotnet/desktop/wpf/advanced/threading-model)
- [dotnet publish](https://learn.microsoft.com/en-us/dotnet/core/tools/dotnet-publish)
- [.NET RID catalog](https://learn.microsoft.com/en-us/dotnet/core/rid-catalog)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Microsoft Learn is rolling and version-selectable; prove SDK/runtime, target framework, desktop framework, RID, OS/architecture, publish properties, and native/COM versions.
- Do not infer .NET 5+ `AssemblyLoadContext` guidance for .NET Framework or generalize WPF dispatcher rules to other UI frameworks.
- Documentation does not prove project reachability, native ABI correctness, COM registration/apartment state, target-host availability, or production performance.

## Required Record

- Record the runtime and publish target, reachability/loading owner, ABI/apartment/dispatcher contract, exercised target artifact, proof limits, and residual risk.
