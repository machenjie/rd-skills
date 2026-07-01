# Go Benchmarks And Patterns

## Baseline Standards

- Use Go project guidance first: Effective Go, Go Code Review Comments, Go memory model, `go vet`, `gofmt`, `goimports`, `govulncheck`, and the repository's pinned `golangci-lint` profile.
- Treat version pins in `SKILL.md` as minimum review baselines, not permanent recommendations; defer to the repository toolchain when it is newer and supported.
- Prefer standard library capabilities before adding dependencies; require a module graph reason for every new package.

## Idiom Patterns

- Pass `context.Context` as the first parameter for request-scoped work; never store it in long-lived structs.
- Use `errgroup` plus bounded fan-out for concurrent subwork; pair every goroutine with owner, cancellation, bound, and error path.
- Use `time.NewTimer` or `time.NewTicker` with `Stop`/`Reset` ownership in loops; avoid unbounded `time.After` allocation.
- Keep interfaces consumer-owned and narrow; prefer concrete types until a second real implementation or test boundary proves the seam.
- Wrap errors with `%w` across layers and assert caller-visible behavior with `errors.Is` or `errors.As`.
- Configure production HTTP servers with read, write, idle, header, body, and shutdown timeouts.
- Size `database/sql` pools intentionally; use context-aware calls and close `Rows`/`Body` at the acquisition boundary.

## Deviation Record

Use this compact record when accepting a non-standard Go choice:

```markdown
Go Deviation
- Rule:
- Reason:
- Scope:
- Owner:
- Expiration or cleanup trigger:
- Validation proving the exception is bounded:
```
