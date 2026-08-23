# Resource Lifecycle and Error Contracts

Use this Reference only for the named low-level resource-lifecycle-and-error-contracts decision.

## Decision Rules

- Track acquisition, transfer, exhaustion, and release of descriptors, sockets, handles, memory, threads, timers, mappings, temporary files, and kernel objects across partial initialization and shutdown.
- Preserve causal diagnostics and protocol state across error translation and retry while excluding secrets and invalid or partially initialized data.
