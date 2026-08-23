# C# Async, Resource, And Iterator Contracts

Use this Reference for a C# execution, cleanup, enumeration, null, copy, or DI-lifetime decision.

## Boundary Decisions

| Boundary | Required contract |
| --- | --- |
| Async owner | Observed task, caller token/deadline, context/dispatcher, exception, result cardinality, shutdown. |
| Cancellation | Token propagation, cancellation-versus-fault, cleanup, irreversible work around cancellation. |
| Resource | `IDisposable`/`IAsyncDisposable` owner, construction/reverse cleanup, repeated cleanup, concurrent use, primary-versus-cleanup failure. |
| Iterator | First execution, enumeration/disposal sites, partial enumeration, mutation, failure timing, resource across `yield`. |
| Async iterator | `[EnumeratorCancellation]`/token flow, cleanup, abandonment, backpressure, failure after elements. |
| LINQ/provider | `IEnumerable<T>`/`IQueryable<T>`, deferred/materialized work, translation/client execution, query count/order, repeated effects. |
| Nullable | Context/warnings plus runtime checks for reflection, serialization, interop, generated/oblivious code, collection elements. |
| Type/value | Class/struct/record equality/copy graph and `ValueTask` consumption. |
| DI | Service lifetime/capture, scope/disposal, and container owner. |

## Failure Probes

| Probe | Required cases |
| --- | --- |
| Async | Pre-start/suspended cancellation, unawaited-child fault, UI/context caller without blocking waits. |
| Cleanup/enumeration | Construction/primary/cleanup failures, abandoned iterator, deferred work enumerated twice. |
| Type/DI | Runtime null, nested-record mutation, struct box/copy, scoped service through each owner. |

## Primary Sources

[async](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios), [cancellation](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken), [dispose](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-disposeasync), [iterators](https://learn.microsoft.com/en-us/dotnet/csharp/iterators), [LINQ](https://learn.microsoft.com/en-us/dotnet/csharp/linq/), [nullable](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types), [records](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records), [DI](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/service-lifetimes). Accessed 2026-07-24.

## Proof Limits

Rolling sources require language/nullable settings, framework/runtime, provider, container, and UI host evidence. They do not prove translation, cancellation support, ownership, allocation, runtime null safety, GC cleanup, or repeated consumption.

## Required Record And Rejections

- Record owners, token/error/cleanup outcomes, enumeration/null/type boundaries, DI lifetime, failure paths, limits, residual risk.
- Reject hidden async failure, sync-over-async, or cleanup-order claims without failure-path proof.
