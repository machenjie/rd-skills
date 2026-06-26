# CLI Daemon Interface Design Benchmarks And Patterns

Use this reference when `cli-daemon-interface-design` needs more detail than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, evidence, output, and gates; use this file for command grammar patterns, output compatibility, daemon lifecycle, dry-run/idempotency, TUI/non-TTY behavior, graph/memory/trajectory coupling, and anti-pattern review.

## Benchmark Anchors

- POSIX Utility Conventions and GNU CLI practice: predictable options, `--`, `--help`, `--version`, and long-option discoverability.
- clig.dev: helpful defaults, composable output, error messages that support recovery, and respectful terminal behavior.
- Git porcelain, Docker `--format`, AWS CLI `--output`, and kubectl dry-run modes: machine-readable output and compatibility tiers.
- JSON Lines and RFC 7464: streamable event records for long-running commands.
- systemd `Type=notify`, launchd, Windows Service Control Manager, Kubernetes readiness/liveness, and tiny init for containers: daemon lifecycle expectations.
- Sysexits and Unix signal exit conventions: meaningful exit classes for automation and retry decisions.
- Twelve-Factor config and logs: deterministic env/config precedence and logs as event streams.
- OpenTelemetry logs: structured daemon diagnostics with correlation and bounded labels.

## Interface Mode Decision Matrix

| Interface type | Primary contract | Evidence required | Common failure |
| --- | --- | --- | --- |
| One-shot human command | Clear command grammar and help. | Help text, examples, usage-error exit code. | Human-only output later parsed by scripts. |
| Automation command | Stable machine output and retryable exit codes. | Schema, golden output, stderr separation, compatibility window. | Progress or warnings on stdout. |
| Destructive operator tool | Target scoping, dry-run, confirmation, idempotency. | No-write dry-run proof, target-validation test, rerun behavior. | `--force` deletes the wrong target. |
| Streaming command | Event schema, ordering, backpressure/cancel behavior. | JSONL schema, interrupted-stream behavior, partial output policy. | Partial human prose breaks consumers. |
| Long-running daemon | Lifecycle, readiness, reload, drain, cleanup. | Supervisor config, signal tests, readiness/liveness proof. | Ready before dependencies or no graceful shutdown. |
| TUI/wizard | Keyboard/cancel/non-TTY behavior and terminal restoration. | TTY/non-TTY tests, resize/cancel behavior, terminal reset proof. | CI hangs waiting for input. |

## Command Grammar And Compatibility

| Decision | Strong pattern | Evidence |
| --- | --- | --- |
| Subcommands | Verb-noun or domain-noun hierarchy with stable aliases only when needed. | Command tree and deprecation map. |
| Positional args | Required identity values only; avoid overloaded positionals. | Usage examples and invalid-argument tests. |
| Flags | Long names for clarity, short aliases only for common safe actions. | Flag matrix with defaults and validation. |
| Deprecated forms | Hidden or warned form with removal version. | Compatibility test and migration note. |
| Experimental behavior | Explicit stability tier or namespace. | Help text and docs mark beta/experimental. |
| Non-local target | Require `--profile`, `--context`, `--cluster`, `--tenant`, or equivalent. | Target-validation test blocks implicit production. |

## Output Contract Patterns

| Output mode | Use when | Stability rule | Test pattern |
| --- | --- | --- | --- |
| Human table/prose | Interactive inspection only. | May change between minor versions unless documented. | Snapshot or help/example review. |
| JSON | Automation reads one complete result. | Additive fields allowed; removals need compatibility window. | `cmd --output json 2>/dev/null | jq .`. |
| JSONL / NDJSON | Streaming events or long-running progress. | One valid JSON object per line; event type is stable. | Parse every line and assert terminal event. |
| TSV | Simple shell pipelines. | Stable columns and escaping documented. | Golden column order test. |
| YAML | Human-readable structured config. | Stable keys where used by automation. | Schema or parser test. |
| Porcelain | Backward-compatible script output. | Versioned contract; breaking changes require new mode. | Consumer fixture and golden diff. |

Diagnostics, warnings, logs, prompts, and progress belong on stderr. Structured machine output must remain valid when stderr is redirected away.

## Exit Code Taxonomy

| Code | Meaning | Retry guidance |
| --- | --- | --- |
| 0 | Success. | Do not retry. |
| 1 | Generic or unexpected failure. | Retry only when stderr identifies a transient cause. |
| 2 | Usage or argument error. | Do not retry without changing invocation. |
| 3 | Validation error. | Do not retry until input/config changes. |
| 4 | Partial success. | Run repair/status command before retry. |
| 5 | External dependency unavailable. | Retry with backoff if idempotent. |
| 6 | Precondition failed or target state mismatch. | Inspect status and reconcile. |
| 124 | Timeout. | Retry only when operation is idempotent and timeout budget changes. |
| 126 | Command found but not executable. | Fix installation/permissions. |
| 127 | Command not found. | Fix installation/PATH. |
| 130 | Interrupted by SIGINT. | Safe to inspect status; retry only after cleanup. |
| 137 | SIGKILL/OOM. | Treat as incomplete; inspect side effects. |
| 143 | SIGTERM. | Expected shutdown path for daemons and containers. |

## Dry-Run And Idempotency

Strong destructive/operator tools define:

- the side-effect boundary where dry-run stops;
- whether dry-run validates remote permissions, target existence, quota, and schema;
- scoped target selector and explicit confirmation token;
- idempotency key, lock, checkpoint, or status command for reruns;
- partial-failure repair command and rollback/compensation path;
- audit output that is safe to store and contains no secrets.

Anti-pattern: dry-run builds a separate fake plan that does not exercise validation. Safer pattern: share discovery and validation code paths, then replace the final mutation adapter with a no-write adapter.

## Daemon Lifecycle Matrix

| Lifecycle concern | Strong pattern | Evidence |
| --- | --- | --- |
| Start | Validate config, acquire lock, initialize dependencies, then report ready. | Startup integration test and ready signal. |
| Readiness | Ready only after listener and dependencies are usable. | `/readyz`, `sd_notify(READY=1)`, or platform equivalent test. |
| Liveness | Process health distinct from dependency readiness. | `/livez` or supervisor heartbeat. |
| Reload | Parse and validate new config before atomic swap. | Invalid reload keeps prior config and warns. |
| SIGTERM | Stop intake, drain in-flight work, flush logs, release locks. | `kill -TERM` test with timeout. |
| SIGINT | User cancel cleanup with exit 130. | Integration test or signal handler review. |
| Child processes | Forward signals and reap children. | PID 1/tiny-init or explicit reaper proof. |
| PID/lock | Kernel-backed `flock`/`fcntl`; PID is diagnostic only. | Concurrent start test and stale PID behavior. |

## Config Precedence And Runtime Policy

Prefer deterministic precedence:

1. built-in defaults;
2. system config;
3. user config;
4. project config;
5. environment variables;
6. command-line flags.

Secrets are not ordinary config: read from env, file, stdin, keychain, or secret store, never from positional args or short flags. For hot reload, validate the complete new config before apply and keep the last good config on failure.

## TUI And Non-TTY Behavior

Terminal interactions need an explicit non-interactive contract:

- detect stdin/stderr TTY separately;
- require `--yes`, `--assume-yes`, or `--non-interactive` for CI paths;
- send progress and prompts to stderr;
- restore terminal mode on success, error, panic, SIGINT, and SIGTERM;
- define Escape/Ctrl-C behavior and exit code;
- handle resize with `SIGWINCH` where supported;
- avoid color unless TTY or `FORCE_COLOR`; honor `NO_COLOR`.

## Graph, Memory, And Trajectory Coupling

Treat repository graph, project memory, and execution trajectory as discovery inputs until current source confirms them.

| Input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current commands, docs, generated help, tests, scripts, service units, and consumers are inspected. | Graph proximity is treated as proof of command compatibility. |
| Project memory | Prior command semantics still match current source, docs, and automation consumers. | Memory predates a flag rename, output schema change, supervisor change, or script migration. |
| Execution trajectory | Validation ran after the final interface edit and covered changed command behavior. | Output predates the current change or covers only unrelated validators. |
| Generated help/docs | Regenerated or inspected after command changes. | Help text is assumed from stale examples. |
| Automation consumers | CI, cron, release scripts, docs, or customer scripts are listed and compatibility classified. | Unknown consumers are ignored instead of named as residual risk. |

Strong outputs state which graph, memory, and trajectory inputs were accepted, rejected, or left unknown.

## Validation Evidence Patterns

- Command grammar: help snapshot, invalid-arg tests, deprecated alias compatibility.
- Machine output: schema test, golden JSON/JSONL/TSV output, parser smoke test with stderr discarded.
- Exit codes: matrix test for usage, validation, dependency, partial success, timeout, and signal cases.
- Config precedence: default/file/env/flag matrix with production target guard.
- Dry-run: assert no remote mutation, file write, credential rotation, publish, delete, or migration side effect.
- Idempotency: rerun after partial checkpoint or already-applied state.
- Daemon lifecycle: signal tests for SIGTERM/SIGINT/SIGHUP, readiness/liveness, lock release, child reaping.
- TUI/non-TTY: CI non-interactive path, cancellation, resize, color suppression, terminal restoration.
- Security: no secrets in argv/help/logs/errors, redaction checks, permission/sandbox record for operator tools.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Human table is the only output and scripts parse columns. | Column/prose change breaks automation. | Add stable JSON/porcelain mode and consumer tests. |
| Warnings and progress written to stdout. | `jq`, `awk`, or CI parser fails. | Send diagnostics to stderr and test stdout purity. |
| Every error returns exit 1. | Automation retries terminal failures forever. | Exit-code taxonomy with retry guidance. |
| `--force` is the only destructive guard. | Operator confirms the wrong target. | Scoped selector, confirmation token, dry-run, and target validation. |
| Secret accepted as `--token value`. | Secret leaks through shell history and process list. | Env/file/stdin or secret store. |
| Daemon reports ready before dependencies. | Load balancer sends traffic to dead instance. | Ready after dependency checks; live remains process health. |
| SIGHUP applies invalid config partially. | Process crashes or runs mixed settings. | Parse-then-swap with last-good fallback. |
| PID file used as lock. | Stale PID blocks startup or permits double start. | Kernel lock plus PID for diagnostics only. |
| TUI prompt in CI without non-TTY path. | Pipeline hangs. | Non-interactive flag or fail with usage error. |

## Handoff Boundaries

- Use `shell-cli-professional-usage` when the unresolved work is shell quoting, traps, temp files, or script implementation.
- Use `configuration-runtime-policy` when config/flag ownership, expiry, cleanup, hot reload, or runtime switch governance is the primary concern.
- Use `contract-testing` or `consumer-impact-analysis` when output schema consumers need compatibility proof.
- Use `security-privacy-gate` when secrets, IAM, auth, path/URL validation, or privileged operation is in scope.
- Use `reliability-observability-gate` when daemon readiness, shutdown, telemetry, SLOs, or on-call behavior is in scope.
- Use `delivery-release-gate` when the command deploys, migrates, publishes, rolls back, or mutates production.
