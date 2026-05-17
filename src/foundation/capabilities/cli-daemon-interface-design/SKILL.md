---
name: cli-daemon-interface-design
description: Designs CLI, TUI, and daemon interfaces with command semantics, flags, config precedence, stdout/stderr contracts, exit codes, signals, dry-run behavior, logging, idempotency, and scriptability.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "98"
changeforge_version: 0.1.0
---

# Mission

Design command-line, TUI, and daemon interfaces that are predictable for humans, safe for automation, observable in operations, and resilient under reruns, signals, partial failure, and configuration drift.

# Pinned Tooling Baseline

- Argument parsing libraries: Go `spf13/cobra` v1.8 + `spf13/viper` v1.18; Python `click` ≥ 8.1 or `typer` ≥ 0.12; Rust `clap` v4 (derive); Node `commander` v12 or `yargs` v17; Java `picocli` ≥ 4.7; .NET `System.CommandLine` ≥ 2.0.
- Output conventions: human format on stdout by default; `--output json|jsonl|yaml|tsv` for machine output; NDJSON / JSON Lines (RFC 7464 / jsonlines.org) for streaming events.
- Daemon supervision: systemd unit with `Type=notify` and `sd_notify(READY=1)`; macOS `launchd` plist; Windows Service Control Manager via `sc.exe` or `WindowsService` host; container PID 1 must reap zombies or run under `tini`/`dumb-init`.
- Lifecycle primitives: PID file under `/run/<name>.pid` with `flock(LOCK_EX|LOCK_NB)`; Unix domain socket or named pipe for control plane; `SIGHUP` for config reload; `SIGTERM` then `SIGKILL` with documented grace period (default 30 s, aligned with systemd `TimeoutStopSec`).
- Logging baseline: structured logs (JSON) to stderr; OpenTelemetry Logs SDK or equivalent; `--log-level` flag and `LOG_LEVEL` env aligned with `RFC 5424` severities; no secrets in `--help`, no secrets in process arg list.
- Help and version contract: `--help` / `-h`, `--version`, `--config <path>`, `--quiet`/`--verbose`, `--no-color`, `NO_COLOR` env (no-color.org), `FORCE_COLOR` only when explicitly requested.

# When To Use

Use this capability when a change adds or modifies commands, subcommands, flags, positional arguments, config files, environment variables, TUI workflows, daemon lifecycle behavior, background process behavior, stdout/stderr output, logging, exit codes, signal handling, dry-run behavior, or scriptable machine output.

# Do Not Use When

Do not use this capability for generic shell safety alone; use `shell-cli-professional-usage` for script implementation details. Do not use it for HTTP API contracts, package contracts, or background job design unless the user-facing interface is a CLI, TUI, or daemon boundary.

# Non-Negotiable Rules

- Define command semantics, argument grammar, config precedence, output contract, exit-code table, and failure behavior before implementation.
- Keep stdout for requested command output and stderr for diagnostics, progress, warnings, and errors; never interleave structured machine output with progress on the same stream.
- Provide a machine-readable output mode (`--output json` or NDJSON) for every command whose output may be parsed; document the stability guarantee.
- Define `--dry-run` for any command that mutates remote state, writes outside the working directory, or rotates credentials; dry-run must exercise the same code paths up to the side-effect boundary.
- Make reruns idempotent or explicitly document non-idempotent effects, required selectors, and detection of partial prior runs.
- Handle `SIGINT` and `SIGTERM` with cleanup, lock release, in-flight request drain, and a deterministic non-zero exit code (`130` for SIGINT, `143` for SIGTERM by Unix convention).
- Document daemon lifecycle: start, stop, reload (`SIGHUP`), health, logs, PID/lock behavior, config reload semantics, and graceful shutdown timeout.
- Avoid ambiguous defaults for production targets, destructive operations, credentials, and config locations; require explicit `--profile`, `--cluster`, or `--context` for non-local targets.
- Never accept secrets as positional args or short flags that appear in shell history and `/proc/<pid>/cmdline`; accept via env, file, or stdin only.

# Industry Benchmarks

- POSIX.1-2017 Utility Conventions (single-letter options, `--` argument terminator).
- GNU Coding Standards: Command-Line Interfaces (long options, `--help` / `--version`).
- Command Line Interface Guidelines (clig.dev, 2022).
- systemd `sd_notify` readiness protocol and `Type=notify` service unit.
- 12-Factor App III. Config (env-var precedence) and XI. Logs (event streams to stderr).
- JSON Lines (jsonlines.org) for streamable machine output.
- OpenTelemetry Logs Data Model 1.x for daemon log enrichment.
- Kubernetes `kubectl` `--dry-run=client|server`, Docker `--format`, AWS CLI `--output`, Git `--porcelain` for stable machine output precedent.
- Sysexits(3) and `bash(1)` exit-code conventions (`0`, `1`, `2`, `64-78`, `126-130`, `137`, `143`).

# Selection Rules

Select this capability when the primary design risk is an operator or automation interface. Pair with `shell-cli-professional-usage` for shell implementation, `delivery-release-gate` for release tooling, `backend-change-builder` for daemon internals, `logging-error-handling` for diagnostics, and `quality-test-gate` for command behavior tests.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when the command rotates secrets, prints credentials, accepts auth via flag, or invokes IAM mutations.
- Escalate to `delivery-release-gate` when the command performs deploys, migrations, publishes artifacts, or touches production state.
- Escalate to `reliability-observability-gate` when it spawns a long-running daemon, accepts unattended CI input, or affects on-call signal.
- Escalate to `data-api-contract-changer` when machine output is consumed by other services and the schema is changing without a compatibility window.

# Critical Details

- Config precedence must be deterministic and documented: built-in defaults → system config (`/etc/<name>/config.yaml`) → user config (`$XDG_CONFIG_HOME/<name>/`) → project config (`./.<name>.yaml`) → env vars (`<NAME>_*`) → flags. Higher overrides lower.
- Interactive prompts must detect non-TTY (`isatty(0)` / `isatty(2)`) and either consume `--yes`/`--assume-yes` or fail with exit 2 in CI; never silently default to destructive `Y`.
- `--force` is never sufficient by itself; require either a scoped selector (`--cluster`, `--namespace`), an evidence flag (`--confirm <name>`), or prior dry-run.
- Progress indicators (spinners, bars) must go to stderr and detect TTY; suppress under `--quiet`, `--output json`, or `NO_COLOR`.
- Exit code table (recommended): `0` success; `1` generic failure; `2` usage error; `3` validation error; `4` partial success; `5` external dependency unavailable; `6` precondition failed; `124` timeout (GNU coreutils); `125`-`128` reserved; `130` SIGINT; `143` SIGTERM; `137` SIGKILL/OOM.
- Daemons must report readiness only after dependencies are reachable, migrations are applied, and the listener is accepting connections; for systemd use `sd_notify(READY=1)`, for Kubernetes serve `/readyz` distinct from `/livez`.
- Config reload (`SIGHUP`) must be atomic: parse-then-swap; an invalid reload must keep the prior config and emit a warning, never crash the process.
- TUI flows must preserve keyboard accessibility (Tab order, Escape exit), restore terminal mode on every exit path (including panic), and survive `SIGWINCH` (resize).
- Lock files must be released by the kernel on process exit (use `flock`/`fcntl`, not stale-mtime files) and must store PID for diagnostics, not for locking.
- For containers, run as PID 1 only with a tiny init (`tini`, `dumb-init`); otherwise zombie reaping and signal forwarding break.

# Failure Modes

- Symptom: automation breaks after a CLI release.
  Cause: scripts parse human stdout (column alignment, prose).
  Detection: golden-output diff in CI plus `--output json` schema test.
  Impact: silent pipeline failure, wrong downstream data.
- Symptom: jq fails parsing output.
  Cause: progress bar or warnings written to stdout instead of stderr.
  Detection: integration test runs `cmd --output json | jq .` with stderr discarded.
  Impact: every CI consumer breaks simultaneously.
- Symptom: production deploy ran with the wrong cluster.
  Cause: config file silently overrode flag, or default profile was unscoped.
  Detection: precedence unit tests; require `--cluster` for production.
  Impact: cross-environment data loss.
- Symptom: `rm`-style command had no dry-run and removed user data.
  Cause: only `--force` guard; no scoped selector.
  Detection: code review checklist; presence of `--dry-run` test.
  Impact: irrecoverable user data loss.
- Symptom: daemon hangs on shutdown and is killed by orchestrator.
  Cause: no SIGTERM handler, blocking I/O without cancellation.
  Detection: shutdown integration test with `kill -TERM` and timeout assertion.
  Impact: in-flight requests dropped, transaction inconsistency, on-call paging.
- Symptom: load balancer routes to dead replica.
  Cause: daemon reports ready before downstream connections established.
  Detection: readiness probe distinct from liveness; integration test.
  Impact: 5xx burst during rollout.
- Symptom: every failure exits `1`, retry logic re-runs validation errors forever.
  Cause: collapsed exit-code taxonomy.
  Detection: exit-code unit tests per failure class.
  Impact: runaway retry storms, alert noise.
- Symptom: secret leaked to shell history and process listing.
  Cause: secret accepted as `--token <value>`.
  Detection: lint rule banning secret-named flags; require `--token-file` / `<NAME>_TOKEN` env.
  Impact: credential disclosure on shared hosts.

# Output Contract

Return a CLI/TUI/daemon interface design with:

- `command_model`: commands, subcommands, positional args, flags, aliases, hidden/deprecated commands, stability tier (stable/beta/experimental)
- `config_precedence`: ordered list of defaults, config files, env vars, flags, secrets, profile selection
- `output_contract`: stdout format per command, stderr diagnostics format, machine-readable mode schema reference, stability guarantee window
- `exit_codes`: numeric table with meaning, retry guidance, and signal mapping
- `safety_controls`: dry-run behavior, confirmation strategy, target scoping flags, idempotency keys, lock and temp-file ownership
- `signal_lifecycle`: `SIGINT` / `SIGTERM` / `SIGHUP` / `SIGUSR1` behavior, drain timeout, cleanup order
- `daemon_behavior`: start/stop/status/reload, readiness vs liveness, structured log schema, PID/lock path, supervision target (systemd/launchd/k8s)
- `tests`: golden output, exit-code matrix, config precedence, signal/drain, idempotency/rerun, dry-run honesty, TTY-vs-pipe behavior
- `documentation`: command help, examples for each command, deprecation notes with removal version, automation contract reference

# Quality Gate

1. Every command exposes `--help`, `--version`, and a machine-readable output mode where output is parseable.
2. Stdout / stderr separation is verified by a `cmd ... 2>/dev/null | jq .` style test.
3. The exit-code table has at least 5 distinct classes and each is covered by a test.
4. Every destructive command has a `--dry-run`, a scoped selector, and a confirmation gate, and tests assert dry-run performs no remote mutations.
5. Config precedence is asserted by a test matrix (default vs env vs flag vs file).
6. `SIGTERM` shutdown completes within the documented grace period in an integration test; locks released afterward.
7. For daemons, readiness is distinct from liveness and only flips ready after dependencies pass.
8. No flag or positional arg accepts a secret value; secret intake routes through env, file, or stdin and is asserted by a lint rule.
9. Help text discoverability is reviewed: each subcommand has a runnable example and a deprecation note where applicable.

# Used By

- backend-change-builder
- integration-change-builder
- delivery-release-gate
- quality-test-gate
- shell-cli-professional-usage

# Handoff

Hand off to `shell-cli-professional-usage` for shell implementation, `logging-error-handling` for diagnostics and redaction, `async-job-design` for background work semantics, `delivery-release-gate` for operational rollout, and `quality-test-gate` for command behavior coverage.

# Completion Criteria

The capability is complete when the command or daemon interface is scriptable, documented, idempotency-aware, signal-safe, config-deterministic, observable, secret-safe, and covered by tests that protect output, exit-code compatibility, and lifecycle behavior.
