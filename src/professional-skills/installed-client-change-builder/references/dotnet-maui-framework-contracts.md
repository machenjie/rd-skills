# .NET MAUI Framework Contracts

Use this Reference only for the named dotnet-maui-framework-contracts decision.

## Decision Rules

- Map cross-platform window events to the affected native lifecycle.
- Validate platform lifecycle hooks, restored state, permissions, and each package target.

## Sources And Version Limit

Source: [.NET MAUI app lifecycle](https://learn.microsoft.com/en-us/dotnet/maui/fundamentals/app-lifecycle).
Version limit: the recorded page resolves to .NET MAUI 10.0. Pin the repository's target frameworks, workloads, native SDKs, and packaging configuration.
