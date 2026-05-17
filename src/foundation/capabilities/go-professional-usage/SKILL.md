---
name: go-professional-usage
description: Use when writing or reviewing professional Go for services, CLIs, libraries, workers, or infrastructure tools, with focus on context propagation, errors, goroutine lifecycle, interfaces, table tests, race testing, package boundaries, and deployment simplicity.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "89"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Go usage for services, CLIs, libraries, workers, and infrastructure tooling: context propagation, error wrapping, goroutine lifecycle, small consumer-defined interfaces, table-driven tests, race-detector evidence, package boundaries, structured logging, dependency management, and simple deployment artifacts. Reject Java-style over-abstraction and Python-style dynamic dispatch translated into Go.

# Pinned Tooling Baseline (Go)

- **Toolchain**: Go ≥ 1.22 (1.23 preferred). Go 1.21 acceptable only with documented reason. **Go 1.20 and below are unsupported by the Go team — rejected.**
- **Module mode**: required; `GOPATH` mode is forbidden for new work.
- **Formatter**: `gofmt` + `goimports` (or `golangci-lint run` invoking the format check). Non-gofmt code is rejected by CI.
- **Linter**: `golangci-lint` ≥ v1.60 with enabled linters at minimum: `govet`, `staticcheck`, `errcheck`, `ineffassign`, `unused`, `gosimple`, `gosec`, `revive`, `bodyclose`, `noctx`, `sloglint`, `nilerr`, `contextcheck`.
- **Vulnerability scanning**: `govulncheck ./...` in CI (Go team's official tool).
- **Race detector**: `go test -race -count=N` mandatory for any concurrent code change (N ≥ 5 for stress).
- **Logging**: `log/slog` (stdlib, Go 1.21+) with structured handler; older `log` package rejected for services.
- **Test framework**: stdlib `testing` + `testify/require` (sparingly, prefer stdlib + helper funcs); table-driven test pattern; `t.Parallel()` where safe.
- **Build**: reproducible `-trimpath -buildvcs=true` + `-ldflags '-buildid='` for deterministic artifacts; static binary unless explicitly required otherwise.
- **Module file**: `go.mod` with `go <minor>` directive matching toolchain; `go.sum` checked in; `GOFLAGS=-mod=readonly` in CI.

# When To Use

Use when Go code is added, reviewed, refactored, AI-generated, or tested. Use whenever a goroutine, channel, context, interface, error, or third-party module is introduced or changed.

# Do Not Use When

Do not use to teach Go syntax. Do not use to force Go where the workload (CPU-heavy ML, complex UI, deep async data flows) points elsewhere.

# Non-Negotiable Rules

- **`context.Context` propagated end-to-end**: handler → service → repository → DB/HTTP/RPC client. No `context.TODO()` outside main / tests / init. No `context.Background()` mid-request. All external calls accept and honor context cancellation.
- **Goroutines have a bounded lifetime and explicit cancellation.** Every `go func(...)` has a documented owner and cancellation mechanism (context, channel, sync.WaitGroup). "Fire and forget" is rejected.
- **Errors wrapped with `%w`** at every layer; root cause preserved; checked with `errors.Is` / `errors.As`. Never `fmt.Errorf("%s", err)` (loses wrap chain).
- **Interfaces defined by consumer, not producer.** Small interfaces (typically 1-3 methods) at the call site; never a 20-method interface in the package that owns the implementation.
- **Table-driven tests** for business logic; subtests via `t.Run`; `t.Parallel()` where safe; `testdata/` for fixtures.
- **Race detector mandatory for concurrent changes**: `go test -race -count=5 -timeout=10m ./...` in CI.
- **No unbounded channels / goroutine fan-out**: bounded worker pool or semaphore; backpressure design explicit.
- **No `panic` in libraries**; `panic` only for truly unrecoverable invariant violation in `main` / init. Recovered panics in HTTP middleware log + return 500.
- **`defer` paired with resource acquisition** on the next line; `defer rows.Close()`, `defer mu.Unlock()`, `defer cancel()`.
- **No global mutable state** except for `var ` + `sync.Once` initialization at startup.

# Industry Benchmarks

- **Effective Go**, **Go Code Review Comments**, **Uber Go Style Guide**, **Google Go Style Guide**.
- **Go memory model** (2022 refresh) for concurrency correctness.
- **Go Proverbs** (Rob Pike): "A little copying is better than a little dependency"; "Make the zero value useful"; "Don't communicate by sharing memory; share memory by communicating".
- **CWE Top 25** — idiomatic Go fixes for SQLi (`database/sql` parameterization), command injection (`exec.Command` with separate args, never `bash -c <str>`), path traversal (`filepath.Clean` + base validation).
- **govulncheck** (Go security team) and **OSV-Scanner** for module vulnerability scanning.
- **OpenTelemetry Go** for tracing; `slog` for structured logs.

# Selection Rules

Select when Go is present or proposed. Pair with `language-idiom-enforcement`, `language-testing-strategy`, `language-performance-safety`, `concurrency-control`, and `package-dependency-management`.

# Risk Escalation Rules

- Escalate to `concurrency-control` for races / deadlocks / goroutine leaks / channel deadlock / pool sizing.
- Escalate to `reliability-observability-gate` for production service behavior, GC pause, p99 latency.
- Escalate to `package-dependency-management` for module changes and `govulncheck` advisories.
- Escalate to `language-performance-safety` for hot-path allocation, pprof analysis, GC pressure.
- Escalate to `security-privacy-gate` for `gosec` findings, command/SQL injection, secrets handling.

# Critical Details

- **Context propagation pitfall**: storing context in a struct (`type S struct { ctx context.Context }`) is an anti-pattern — context flows as a parameter. Storing context invalidates cancellation semantics.
- **Goroutine leak pattern**: goroutine blocked on a send to an unbuffered channel with no receiver; or blocked on a receive from a channel never closed; or blocked on a mutex held by a panicked goroutine. Detection: `go tool pprof http://.../debug/pprof/goroutine` showing monotonic growth.
- **`sync.WaitGroup.Add`** must be called before `go func()`, not inside the goroutine — race condition.
- **`for _, v := range slice { go func() { use(v) } }`** — pre-Go-1.22, loop variable captured by reference — all goroutines see last value. Go 1.22 fixes loop semantics, but be explicit in older code via `v := v` shadow.
- **`errgroup`** (`golang.org/x/sync/errgroup`) for fan-out with first-error semantics; pair with context cancellation.
- **String concatenation** with `+` in loops allocates O(n²); use `strings.Builder` or pre-sized `bytes.Buffer`.
- **`time.After` in `select`** in a loop leaks a timer per iteration; use `time.NewTimer` + `Stop`.
- **`map` iteration order** is randomized; never depend on order. For deterministic output, sort keys.
- **`nil` interface vs nil concrete value**: `var p *T; var i I = p` makes `i != nil` because the interface holds a type pointer. Subtle bug source.
- **HTTP server**: always set `Read/Write/IdleTimeout`; never `http.ListenAndServe(addr, mux)` for production without timeout.
- **DB driver**: always `defer rows.Close()`; always pass context to `QueryContext` / `ExecContext`; bounded `db.SetMaxOpenConns` / `SetMaxIdleConns` / `SetConnMaxLifetime` based on Little's Law.
- **Avoid `init()` for non-trivial logic**: hard to test, runs on import. Prefer explicit `New...()` constructors.
- **Generics (1.18+)**: use sparingly; for genuinely repeated patterns (collections, constraints), not as a substitute for clear concrete types.

# Failure Modes

- **Goroutine leak** — Symptom: memory + goroutine count grow; eventual OOM. Cause: missing context cancellation / unbuffered-channel deadlock. Detection: pprof goroutine. Impact: rolling restart, masked root cause.
- **Context ignored on DB call** — Symptom: cancelled request continues hitting DB; connections held. Cause: `db.Query` instead of `db.QueryContext`. Detection: lint (`noctx`, `contextcheck`). Impact: connection-pool exhaustion under load.
- **Race on shared map** — Symptom: intermittent crash / panic on concurrent map read+write. Cause: shared map without sync. Detection: `go test -race`. Impact: panic, data corruption.
- **Goroutine per request, unbounded** — Symptom: OOM during traffic spike. Cause: `go handle(req)` without bounded pool. Detection: load test, pprof goroutine count. Impact: cascading failure.
- **`time.After` leak** — Symptom: memory grows in long-running select loop. Cause: `time.After` in loop. Detection: pprof heap. Impact: slow leak, eventual OOM.
- **String concat O(n²)** — Symptom: hot path slow on large inputs. Cause: `s += part` in loop. Detection: pprof CPU. Impact: latency cliff at scale.
- **`%s` instead of `%w`** — Symptom: `errors.Is(err, ErrFoo)` returns false despite wrapping. Cause: `fmt.Errorf("...: %s", err)`. Detection: errcheck / review. Impact: error-handling branches silently dead.
- **Interface-by-producer** — Symptom: 20-method interface in `internal/` package; only 1 implementation; tests use generated mocks of 20 methods. Cause: Java-style abstraction. Detection: code review. Impact: hard-to-change tests, no abstraction value.
- **HTTP server without timeouts** — Symptom: slowloris / connection exhaustion. Cause: `http.ListenAndServe` defaults. Detection: production review. Impact: DoS exposure.
- **`init()` overuse** — Symptom: tests can't isolate; import order matters. Cause: business logic in init. Detection: refactor to explicit constructors. Impact: test fragility.

# Output Contract

Return a **Go Usage Review** containing:
- **Toolchain**: Go version, `go.mod` `go` directive, `go.sum` integrity
- **Tooling pins**: golangci-lint version + enabled linters; govulncheck status; race-detector CI command
- **Context flow**: every external call site receives and honors context; no `context.TODO` outside main/tests
- **Goroutine lifecycle**: each `go func(...)` listed with owner + cancellation mechanism + bound
- **Error handling**: `%w` discipline; sentinel + `errors.Is/As`; no swallowed errors
- **Interface boundaries**: defined by consumer; minimal method count; no abstraction without ≥ 2 implementations
- **Concurrency safety**: race-detector run command and output; lock scope; channel discipline; pool sizing (Little's Law)
- **Dependency impact**: `go mod tidy` clean; `govulncheck` clean or triaged; `go mod why` for new deps
- **Tests**: table-driven coverage; `-race -count=N` in CI; subtests with `t.Parallel()` where safe
- **HTTP/server config**: timeouts, max body size, graceful shutdown
- **DB config**: connection pool sized per Little's Law; context on all queries; `defer Close()` on rows
- **Logging**: `slog` structured; no secrets; correlation/trace IDs propagated
- **Build & deploy**: reproducible flags; static binary; image size
- **Accepted exceptions** with owner / scope / expiration

# Quality Gate

1. Go version ≥ 1.22 (or documented exception); `go.mod` `go` directive matches.
2. `gofmt -l` empty; `golangci-lint run` green with project config; `govulncheck ./...` green or triaged.
3. `go test -race -count=5 ./...` green in CI.
4. Context propagation: no `context.TODO` / `context.Background` outside main / tests / init.
5. Every goroutine has documented owner + cancellation + bound.
6. Errors wrapped with `%w`; root cause preserved; `errors.Is/As` used at handlers.
7. Interfaces defined by consumer; no producer-side mega-interfaces.
8. HTTP server has timeouts; DB pool sized; resources `defer Close()`'d.
9. Tests are table-driven where applicable; `t.Parallel()` used where safe; coverage ≥ 80% line on critical packages.
10. Logging structured via `slog`; secrets never logged.

# Used By

backend-change-builder, integration-change-builder, data-middleware-change-builder, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`concurrency-control`** for races / deadlocks / leaks / channel design / pool sizing.
- **`reliability-observability-gate`** for production SLO concerns.
- **`package-dependency-management`** for module / `govulncheck` action.
- **`language-performance-safety`** for hot-path allocation, pprof analysis.
- **`security-privacy-gate`** for `gosec` findings, secrets, injection.

# Completion Criteria

Review is complete when: toolchain + linter + vuln-scan + race-detector are green; context propagation is end-to-end; every goroutine has a bounded lifetime and cancellation; errors are wrapped and chainable; interfaces are small and consumer-defined; HTTP / DB resources are timed-out and bounded; tests are table-driven and race-checked; and any accepted exception has owner, scope, and expiration.
