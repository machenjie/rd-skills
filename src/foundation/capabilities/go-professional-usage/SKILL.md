---
name: go-professional-usage
description: Use when Go services, CLIs, libraries, workers, infrastructure tools, goroutines, channels, context propagation, errors, interfaces, table tests, race detection, package boundaries, modules, HTTP/DB resources, or deployment artifacts need professional review.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "89"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Go usage for services, CLIs, libraries, workers, and infrastructure tooling: context propagation, error wrapping, goroutine lifecycle, small consumer-defined interfaces, table-driven tests, race-detector evidence, package boundaries, structured logging, dependency management, and simple deployment artifacts. Reject Java-style over-abstraction and Python-style dynamic dispatch translated into Go.

# Pinned Tooling Baseline (Go)

For Go, treat pinned versions as minimum review baselines. If the Go toolchain, linter, scanner, module rule, or deployment flag is EOL, superseded, unsupported, or conflicts with the target project's platform policy, record the project rule and update this capability before using the pin for new work.

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

Use when Go code is added, reviewed, refactored, AI-generated, or tested. Trigger this capability when a goroutine, channel, context, interface, error, `go.mod`, HTTP server, DB client, worker, CLI, package boundary, or third-party module is introduced or changed. Route by the specific boundary and risk: cancellation, leak, race, error semantics, interface ownership, dependency, deploy artifact, or validation freshness.

# Do Not Use When

Do not use to teach Go syntax. Do not use to force Go where the workload (CPU-heavy ML, complex UI, deep async data flows) points elsewhere.

# Stage Fit

Use during Go implementation planning, coding, bug-fix, code-review, refactoring, testing, and release-readiness review. Per-stage focus:

- **coding**: context propagation, error wrapping, defer/resource cleanup, goroutine lifecycle, small interfaces, package boundary.
- **debugging-diagnosis**: race, goroutine leak, context cancellation, wrapped-error loss, deadlock.
- **code-review**: premature interfaces, hidden shared state, ignored errors, context misuse.
- **refactoring**: package cycle, exported API drift, table-driven test coverage.
- **testing**: race detector, table tests, integration seam.

# Mode Matrix
| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Context and resource review | Handler/service/repository/client path, DB/HTTP/RPC call, body/rows/timer/ticker cleanup. | Preserve cancellation, deadlines, and cleanup across boundaries. | Context-flow map, cleanup owner, `noctx`/`bodyclose` or test output. | `language-idiom-enforcement`, `quality-test-gate` | Local helper-only review. |
| Goroutine and channel review | `go func`, channel, worker pool, fan-out, callback, `errgroup`, timer loop. | Bound lifetime, cancellation, backpressure, and error propagation. | Owner/cancel map, race/stress command, goroutine leak check or not-run reason. | `concurrency-control`, `language-performance-safety` | Sequential-only proof. |
| Error and API boundary review | `%w`, sentinel/type error, handler mapping, CLI exit, package export, public interface. | Keep caller-visible error behavior and package contracts stable. | Error chain examples, `errors.Is/As` test, public package boundary scan. | `failure-contract-design`, `code-review` | String-only error assertions. |
| Dependency and module review | `go.mod`, `go.sum`, new module, generated client, version bump, `go mod tidy`. | Keep MVS, provenance, and vulnerability posture explicit. | `go mod why`, `govulncheck`, tidy diff, accepted-risk owner. | `package-dependency-management`, `security-privacy-gate` | Dependency by convenience. |
| Build and deployment review | Binary flags, container image, service timeouts, graceful shutdown, pprof/metrics. | Keep artifact reproducible and runtime behavior observable. | Build command, timeout/shutdown evidence, pprof/metric or residual risk. | `reliability-observability-gate`, `validation-broker` | One local `go test` as release proof. |

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

Select when Go is present or proposed. Pair with `language-idiom-enforcement`, `language-testing-strategy`, `language-performance-safety`, `concurrency-control`, `package-dependency-management`, and `validation-broker` when commands or reports must be mapped to changed paths. Skip only for gofmt-only, comment-only, or generated-output refreshes with no Go behavior, public package, module, race, resource, or deployment change.

# Proactive Professional Triggers
- **Signal:** request-scoped work calls DB, HTTP, RPC, queue, filesystem, subprocess, or worker code without passing `context.Context`. **Hidden risk:** missing cancellation silently leaks DB/HTTP work, hides connection-pool exhaustion, and produces stale work after caller abort. **Required professional action:** map context flow and reject `context.TODO` or mid-request `context.Background`. **Route to:** `language-idiom-enforcement`, `quality-test-gate`. **Evidence required:** inspected call path, lint or test command, exit code, and skipped boundary disclosure.
- **Signal:** a `go func`, channel, worker pool, timer loop, callback, or `errgroup` is added without owner, cancellation, bound, and error propagation. **Hidden risk:** goroutine leak, deadlock, unbounded fan-out, or lost error appears only under load. **Required professional action:** require lifecycle and backpressure proof before acceptance. **Route to:** `concurrency-control`, `language-performance-safety`. **Evidence required:** owner/cancel map, `go test -race` or stress output, pprof/leak evidence or not-run owner.
- **Signal:** error wrapping, sentinel errors, handler mapping, or CLI exit behavior changes without caller-visible examples. **Hidden risk:** `errors.Is/As` branches silently stop working or clients receive unsafe retry semantics. **Required professional action:** preserve the error chain and test boundary mapping. **Route to:** `failure-contract-design`, `code-review`. **Evidence required:** `%w` path, negative tests, public mapping table, and residual risk.
- **Signal:** interface, package export, internal package, generated mock, or shared helper is introduced before caller ownership is clear. **Hidden risk:** producer-owned mega-interface or shared utility pollution freezes implementation details. **Required professional action:** prove consumer-defined interface need and package placement. **Route to:** `implementation-structure-design`, `code-clarity-maintainability`. **Evidence required:** caller inventory, method count, rejected concrete-type alternative, test boundary.
- **Signal:** `go.mod`, `go.sum`, module replacement, generated client, or dependency version changes without module graph and vulnerability evidence. **Hidden risk:** unverified module graph can pull stale or wrong transitive code through Go MVS and leave a hidden vulnerable dependency permanent. **Required professional action:** review module graph, provenance, and cleanup path. **Route to:** `package-dependency-management`, `security-privacy-gate`. **Evidence required:** `go mod why`, `go mod tidy` diff, `govulncheck` report, accepted-risk owner.
- **Signal:** repository graph, project memory, old incident note, or prior agent output claims a Go path is safe, unused, race-free, or already tested without current source confirmation. **Hidden risk:** stale memory misses generated clients, new call paths, or changed CI commands. **Required professional action:** confirm current files, tests, configs, generated artifacts, and validation freshness. **Route to:** `repository-graph-analysis`, `project-memory-governance`, `agent-execution-discipline`. **Evidence required:** inspected paths, accepted/rejected memory, fresh command, remaining unknowns.

# Risk Escalation Rules

- Escalate to `concurrency-control` for races / deadlocks / goroutine leaks / channel deadlock / pool sizing.
- Escalate to `reliability-observability-gate` for production service behavior, GC pause, p99 latency.
- Escalate to `package-dependency-management` for module changes and `govulncheck` advisories.
- Escalate to `language-performance-safety` for hot-path allocation, pprof analysis, GC pressure.
- Escalate to `security-privacy-gate` for `gosec` findings, command/SQL injection, secrets handling.
- Escalate to `agent-tool-permission-sandbox` when Go test, race, build, module, vuln-scan, generated-client, or artifact commands write outputs, fetch modules, or expose secret-bearing logs.

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

# Reference Loading Policy

Load [references/checklist.md](references/checklist.md) when Go changes touch goroutines, context propagation, shared state, DB/HTTP resources, module dependencies, public package APIs, race-detector evidence, or production service settings. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs command/output mapping, graph and memory freshness, race/vulnerability/build evidence, tool permission boundary, or residual-risk wording. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when Go version/tooling pins, concurrency idioms, module/deployment baselines, or accepted deviations need external-standard anchoring. Use [examples/example-output.md](examples/example-output.md) only when review shape is unclear. Do not load references for a trivial gofmt-only edit or local test name change.

# Output Contract

Return a **Go Usage Review** containing:
- **Mode selected**: context/resource, goroutine/channel, error/API, dependency/module, or build/deployment, with trigger signal
- **Boundaries inspected**: Go packages, exported APIs, handlers, workers, DB/HTTP clients, tests, configs, generated artifacts, module files, and skipped boundaries with reason
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
- **Graph/memory/execution coupling**: repository graph and project-memory claims accepted, rejected, stale, or not verified; prior validation freshness after final edit
- **Validation evidence**: literal command, exit code, validator/report/artifact path, and what the output proves or does not prove
- **Tool permission boundary**: test/race/build/module/vuln-scan/generated-artifact command class, sandbox/approval state, write scope, and secret-output redaction rule
- **Accepted Go deviations** with owner, scope, expiration, and cleanup trigger

# Evidence Contract

A Go change is professionally complete only when the output includes:

- **Context boundary**: `context.Context` propagation, cancellation, timeout, and no `context.TODO()` in production path.
- **Goroutine lifecycle**: ownership, cancellation, error propagation, and leak prevention.
- **Error model**: wrapping with `%w`, sentinel/type errors when needed, and caller-visible behavior.
- **Concurrency proof**: race-prone state, locks/channels/errgroup, and `go test -race` when applicable.
- **Resource cleanup**: `defer Close`, connection/body handling, timer/ticker cleanup.
- **Validation evidence**: `go test`, `go test -race`, lint/staticcheck, `govulncheck`, build, benchmark, validator, or not-verified disclosure with command, exit code, output summary, and report/artifact path.
- **What evidence proves**: the inspected Go runtime and idiom risks are covered.
- **What evidence does not prove**: production traffic, all scheduler interleavings, external dependency behavior, or platform-specific runtime behavior.
- **Graph and memory freshness**: current source, generated artifacts, module files, configs, and prior project-memory claims confirmed or rejected before closure.
- **Go residual risk**: untested scheduler/runtime/platform/dependency path, owner, and next gate.

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
11. Validation report maps each changed Go path to command, exit code, covered risk, stale/not-run targets, and residual owner.
12. Tool permission/sandbox record exists for test, race, build, module, vuln-scan, generated-client, or artifact-writing commands.

# Used By

backend-change-builder, integration-change-builder, data-middleware-change-builder, quality-test-gate, ai-code-review-refactor, language-runtime-selection

# Handoff

- **`concurrency-control`** for races / deadlocks / leaks / channel design / pool sizing.
- **`reliability-observability-gate`** for production SLO concerns.
- **`package-dependency-management`** for module / `govulncheck` action.
- **`language-performance-safety`** for hot-path allocation, pprof analysis.
- **`security-privacy-gate`** for `gosec` findings, secrets, injection.

# Completion Criteria

Review is complete when: toolchain + linter + vuln-scan + race-detector are green with commands and exit codes recorded; context propagation is end-to-end; every goroutine has a bounded lifetime and cancellation; errors are wrapped and chainable; interfaces are small and consumer-defined; graph/memory claims are current-source confirmed; HTTP / DB resources are timed-out and bounded; tests are table-driven and race-checked; and any accepted exception has owner, scope, and expiration.
