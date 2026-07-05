# Benchmark Prompt

## Task

Fix a repository or adapter that creates a new HTTP, DB, or SDK client for each
operation.

## Context

The starter repository has `CustomerRepository` and `PartnerAdapter` methods
that instantiate a client inside every method call, hide network IO behind a
repository-looking method, omit pool sizing, and forget to close response bodies
or streams on error paths.

## Requirements

- Move client or pool construction to the correct lifecycle owner.
- Configure timeout, retry, keep-alive, pool sizing, and shutdown cleanup.
- Close response bodies, streams, cursors, or file handles on all paths.
- Make network/storage IO visible in the adapter/repository pattern decision.
- Add tests or static review checks for cleanup and timeout behavior.

## Constraints

- Do not create a client per operation.
- Do not leak response bodies or streams.
- Do not omit pool sizing.
- Do not hide network IO behind a repository or adapter without declaring it.

## Deliverables

- Lifecycle-managed reusable client or pool.
- Performance-Aware Structure Decision and Design Pattern Decision Record.
- Tests or review evidence for cleanup, timeout, retry, and pool behavior.

## Completion Evidence

- Review evidence shows the client lifecycle owner and shutdown path.
- Response cleanup is covered on success and error paths.
- Pool sizing and timeout/retry behavior are explicit.
