# Go Professional Usage Checklist

- Propagate `context.Context` through DB, HTTP, RPC, and worker calls.
- Bound goroutine lifetime and cancellation.
- Wrap errors with `%w` and preserve root cause.
- Keep interfaces consumer-owned and justified.
- Review package boundaries and avoid over-abstraction.
- Add table-driven tests for business logic.
- Run race detector for concurrency-sensitive changes.
- Check module and deployment artifact impact.
- Confirm repository graph and project-memory claims against current source, generated artifacts, module files, and CI config.
- Record tool permission/sandbox write scope for test, race, build, module, vulnerability, or generated-artifact commands.
