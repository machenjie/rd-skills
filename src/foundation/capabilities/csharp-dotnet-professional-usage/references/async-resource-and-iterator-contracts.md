# C# Async, Resource, And Iterator Contracts

Use this checklist when C# execution, cleanup, enumeration, null, copy, or DI-lifetime semantics change.

## Boundary Checklist

- **Async owner:** identify the returned/observed task, caller token, deadline, synchronization/dispatcher requirement, exception path, progress/result cardinality, and shutdown behavior.
- **Cancellation:** propagate the caller token through supported operations, distinguish cancellation from fault, and define cleanup plus irreversible work around the cancellation point.
- **Resource lifetime:** assign `IDisposable` and `IAsyncDisposable` ownership, construction order, reverse cleanup order, repeated cleanup, concurrent use, and primary-versus-cleanup exception behavior.
- **Iterator:** identify when code first executes, each enumeration and disposal site, partial enumeration, source mutation, failure timing, and resource held across `yield`.
- **Async iterator:** identify `[EnumeratorCancellation]` or explicit token flow, producer cleanup, abandonment, backpressure, and failure after earlier elements.
- **LINQ/provider:** distinguish `IEnumerable<T>` from `IQueryable<T>`, deferred from materialized work, translation from client execution, query count, ordering, and repeated side effects.
- **Nullable boundary:** record nullable context and warnings plus runtime validation for reflection, serialization, interop, generated code, oblivious libraries, and collection elements.
- **Type/DI:** verify class/struct/record equality and copy graph, `ValueTask` consumption constraints, service lifetime, captured dependencies, scope creation/disposal, and container ownership.

## Failure Probes

- Cancel before start and during suspension; fault an unawaited child; run the UI/context-sensitive caller without blocking waits.
- Fail construction and primary work while cleanup also fails; abandon an iterator before completion and enumerate a deferred query twice.
- Supply runtime null from an oblivious boundary, mutate a nested record member, box/copy a struct, and resolve a scoped service through each real owner.

## Primary Sources

- [Asynchronous programming scenarios](https://learn.microsoft.com/en-us/dotnet/csharp/asynchronous-programming/async-scenarios)
- [CancellationToken](https://learn.microsoft.com/en-us/dotnet/api/system.threading.cancellationtoken)
- [Implement the async dispose pattern](https://learn.microsoft.com/en-us/dotnet/standard/garbage-collection/implementing-disposeasync)
- [Iterators](https://learn.microsoft.com/en-us/dotnet/csharp/iterators)
- [LINQ](https://learn.microsoft.com/en-us/dotnet/csharp/linq/)
- [Nullable reference types](https://learn.microsoft.com/en-us/dotnet/csharp/language-reference/builtin-types/nullable-reference-types)
- [Record types](https://learn.microsoft.com/en-us/dotnet/csharp/fundamentals/types/records)
- [Dependency injection service lifetimes](https://learn.microsoft.com/en-us/dotnet/core/extensions/dependency-injection/service-lifetimes)

Official pages in this reference were recorded as accessed on 2026-07-24.

## Version And Inference Limits

- Microsoft Learn is rolling and may describe preview behavior; prove language/nullable settings, target framework, runtime, provider, DI container, and UI host.
- The sources do not prove query translation, cancellation support, resource ownership, or copy/allocation cost in this workload.
- Do not infer runtime null safety from warnings, deterministic cleanup from GC/finalization, or safe repeated consumption from `Task`, `ValueTask`, iterator, or LINQ syntax alone.

## Required Record

- Record execution and resource owners, token/error/cleanup outcomes, enumeration and null/type boundaries, DI lifetime, exercised failure paths, proof limits, and residual risk.
