# Go Evidence Patterns

## Required Evidence

- Source boundary: packages, exported APIs, `internal/` boundaries, generated Go files, `go.mod`, `go.sum`, config, and CI command owner.
- Context/resource evidence: request-to-client call path, timeout/cancel owner, `defer Close` owner, timer/ticker cleanup, and `noctx` or `bodyclose` result when available.
- Goroutine/concurrency evidence: goroutine owner, cancellation path, bound or backpressure rule, error propagation, race-prone state, and `go test -race` or stress output.
- Error/API evidence: `%w` chain, sentinel or typed error boundary, `errors.Is/As` tests, handler/CLI mapping, and retry semantics.
- Dependency evidence: `go mod why`, `go mod tidy` diff, `govulncheck ./...`, replacement rationale, provenance, and accepted-risk owner.
- Build/runtime evidence: Go version, `go` directive, reproducible build flags, HTTP timeouts, graceful shutdown, pprof/metric proof, and platform-specific not-run disclosure.
- Graph/memory freshness: repository graph, project memory, generated artifacts, and prior validation claims accepted, rejected, stale, or not verified.

## Tool Permission Boundary

Classify Go commands as read-only inspection, test-cache write, module/network cache write, source/generated-output write, build artifact write, vulnerability scan, or release publish. State sandbox/approval state, write scope (`HOME`, module cache, source tree, `dist/`, CI workspace), and secret-output redaction rule before using command output as evidence.

## Handoff Shape

```markdown
Go Evidence Record
- Source boundary:
- Context/resource proof:
- Goroutine/concurrency proof:
- Error/API proof:
- Dependency/build proof:
- Graph/memory freshness:
- Tool permission boundary:
- Validation:
- What remains unproved:
- Residual risk:
```

## Blocking Conditions

Block completion when concurrency was changed without race or not-run ownership, context/resource cleanup is only assumed, module changes lack vulnerability evidence, generated Go output has no authority source, project-memory claims are reused without current-source confirmation, or artifact-writing commands lack write-scope and rollback disclosure.
