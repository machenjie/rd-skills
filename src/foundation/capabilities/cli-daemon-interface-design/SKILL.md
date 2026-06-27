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

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

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

# Stage Fit

Own CLI, TUI, and daemon interface contracts during design, implementation review, testing, release readiness, and repair when command semantics, operator safety, scriptability, daemon lifecycle, or machine output compatibility can change. In planning, turn current commands, docs, config files, supervisors, repository graph, project memory, execution trajectory, and automation consumers into a scoped interface contract before implementation. In review, reject ambiguous flags, mixed stdout/stderr, unversioned machine output, unsafe daemon shutdown, stale project-memory command assumptions, and validation evidence that does not cover the changed command behavior. Hand off when the remaining work is shell implementation, daemon internals, deployment rollout, security approval, or production observability.

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

# Mode Matrix

Select the interface mode before designing or approving a command, TUI, daemon, or operator tool.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Command contract | New/changed command, subcommand, flag, argument, alias, help, or deprecation. | Stable semantics, grammar, config precedence, compatibility, and discoverability. | Command tree, flag matrix, help examples, deprecated forms, consumer list. | `shell-cli-professional-usage`, `api-contract-design` when output is consumed externally | Daemon lifecycle unless process behavior changes. |
| Machine output compatibility | `--output`, JSON/JSONL/YAML/TSV, porcelain mode, streaming events, or automation consumer. | Preserve parseability and schema stability while separating diagnostics. | Schema/version, golden output, stdout/stderr proof, consumer compatibility window. | `contract-testing`, `consumer-impact-analysis`, `quality-test-gate` | Human UX polish beyond discoverability. |
| Destructive/operator action | Mutates remote state, deploys, deletes, rotates, migrates, publishes, or touches production. | Dry-run honesty, target scoping, confirmation, idempotency, rollback visibility. | Dry-run trace, scoped selector, confirmation token, rerun behavior, side-effect boundary. | `security-privacy-gate`, `delivery-release-gate`, `agent-tool-permission-sandbox` | Silent defaults or `--force` alone. |
| Daemon lifecycle | Long-running process, service unit, signal handling, readiness, reload, PID/lock, or supervision. | Start/stop/reload semantics, graceful drain, readiness, cleanup, observability. | Supervisor config, signal tests, ready/live distinction, lock/PID behavior, shutdown timeout. | `reliability-observability-gate`, `concurrency-control`, `low-level-systems-extension` when OS/process details matter | One-shot command output. |
| TUI/interactive flow | Terminal UI, prompt, wizard, progress, keyboard navigation, or non-TTY execution. | Accessibility, non-TTY behavior, terminal restoration, progress stream, cancel semantics. | TTY/non-TTY test, keyboard path, resize/cancel behavior, stderr progress proof. | `experience-impact-modeler`, `frontend-testing` when visual states matter | Persisted daemon semantics unless present. |

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

Keep this body focused on mode selection, routing, evidence, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for command grammar patterns, output schemas, daemon lifecycle matrices, dry-run/idempotency design, TUI/non-TTY behavior, graph/memory/trajectory coupling, and anti-pattern detail.

# Selection Rules

Select this capability when the primary design risk is an operator or automation interface. Pair with `shell-cli-professional-usage` for shell implementation, `delivery-release-gate` for release tooling, `backend-change-builder` for daemon internals, `logging-error-handling` for diagnostics, and `quality-test-gate` for command behavior tests.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when the command rotates secrets, prints credentials, accepts auth via flag, or invokes IAM mutations.
- Escalate to `delivery-release-gate` when the command performs deploys, migrations, publishes artifacts, or touches production state.
- Escalate to `reliability-observability-gate` when it spawns a long-running daemon, accepts unattended CI input, or affects on-call signal.
- Escalate to `data-api-contract-changer` when machine output is consumed by other services and the schema is changing without a compatibility window.

# Proactive Professional Triggers

- **Signal:** a command or flag is reused from repository graph, project memory, or prior execution trajectory without reading current help/docs/tests/callers. **Hidden risk:** stale automation contract or deprecated flag becomes encoded into new behavior. **Required professional action:** confirm against current source, generated help, CI scripts, docs, and consumers before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected memory, consumer list, and freshness limits.
- **Signal:** output can be piped, parsed, streamed, or consumed by CI while diagnostics/progress are not explicitly separated. **Hidden risk:** a warning, spinner, or human table breaks automation silently. **Required professional action:** define stdout/stderr and machine schema, then add golden output and pipe tests. **Route to:** `contract-testing`, `quality-test-gate`. **Evidence required:** `cmd --output json 2>/dev/null | jq .` style proof, stderr diagnostic sample, schema compatibility window.
- **Signal:** `--force`, default profile, implicit target, or interactive confirmation guards a destructive or production action. **Hidden risk:** operator runs against the wrong environment or repeats a partial mutation. **Required professional action:** require scoped selector, explicit confirmation token, dry-run, idempotency, and rollback/repair guidance. **Route to:** `delivery-release-gate`, `security-privacy-gate`, `agent-tool-permission-sandbox`. **Evidence required:** dry-run no-write proof, target-validation test, rerun/partial-failure behavior.
- **Signal:** daemon readiness, reload, shutdown, lock, PID file, child process, socket, or signal behavior is undocumented or untested. **Hidden risk:** orchestrator routes traffic early, kills in-flight work, leaks locks, or leaves orphan children. **Required professional action:** define lifecycle state machine and signal/cleanup order. **Route to:** `reliability-observability-gate`, `concurrency-control`, `language-performance-safety`. **Evidence required:** signal integration test, readiness/liveness proof, lock release check, shutdown timeout.
- **Signal:** command accepts secrets, tokens, kube contexts, cloud profiles, file paths, URLs, or untrusted selectors through arguments. **Hidden risk:** credential leakage, injection, path traversal, SSRF, or cross-environment mutation. **Required professional action:** move secrets to env/file/stdin, validate selectors and destinations, redact diagnostics, and classify tool permission/sandbox. **Route to:** `security-privacy-gate`, `input-validation`, `secret-configuration-security`. **Evidence required:** no-secret-in-argv review, validation test, redacted error/log sample, permission/sandbox record.
- **Signal:** TUI/prompt assumes an interactive terminal while CI, pipes, screen readers, resize, cancellation, or non-TTY execution are possible. **Hidden risk:** automation hangs or terminal state is corrupted. **Required professional action:** define non-TTY fail/flag path, keyboard/cancel behavior, and terminal restoration. **Route to:** `experience-impact-modeler`, `quality-test-gate`. **Evidence required:** TTY/non-TTY test, cancel/resize test, terminal-mode restoration proof.

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

- **Human-output parsing:** automation breaks after a CLI release.
  Cause: scripts parse human stdout (column alignment, prose).
  Detection: golden-output diff in CI plus `--output json` schema test.
  Impact: silent pipeline failure, wrong downstream data.
- **Stdout contamination:** `jq` fails parsing output.
  Cause: progress bar or warnings written to stdout instead of stderr.
  Detection: integration test runs `cmd --output json | jq .` with stderr discarded.
  Impact: every CI consumer breaks simultaneously.
- **Wrong target mutation:** production deploy ran with the wrong cluster.
  Cause: config file silently overrode flag, or default profile was unscoped.
  Detection: precedence unit tests; require `--cluster` for production.
  Impact: cross-environment data loss.
- **Missing dry-run boundary:** `rm`-style command had no dry-run and removed user data.
  Cause: only `--force` guard; no scoped selector.
  Detection: code review checklist; presence of `--dry-run` test.
  Impact: irrecoverable user data loss.
- **Unbounded shutdown:** daemon hangs on shutdown and is killed by orchestrator.
  Cause: no SIGTERM handler, blocking I/O without cancellation.
  Detection: shutdown integration test with `kill -TERM` and timeout assertion.
  Impact: in-flight requests dropped, transaction inconsistency, on-call paging.
- **False readiness:** load balancer routes to dead replica.
  Cause: daemon reports ready before downstream connections established.
  Detection: readiness probe distinct from liveness; integration test.
  Impact: 5xx burst during rollout.
- **Collapsed exit taxonomy:** every failure exits `1`, retry logic re-runs validation errors forever.
  Cause: collapsed exit-code taxonomy.
  Detection: exit-code unit tests per failure class.
  Impact: runaway retry storms, alert noise.
- **Secret in argv:** secret leaked to shell history and process listing.
  Cause: secret accepted as `--token <value>`.
  Detection: lint rule banning secret-named flags; require `--token-file` / `<NAME>_TOKEN` env.
  Impact: credential disclosure on shared hosts.

# Reference Loading Policy

The `SKILL.md` body carries normal L1/L2 command, TUI, and daemon interface selection, evidence, and quality-gate rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete command or daemon interface, when dry-run/config/output/signal coverage is uncertain, or before implementation starts. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when command grammar, output compatibility, daemon lifecycle, destructive-action safety, TUI/non-TTY behavior, graph/memory/trajectory reuse, or anti-pattern detail needs depth. Load [references/evidence-patterns.md](references/evidence-patterns.md) when closure depends on repository graph, project memory, execution trajectory, validation freshness, command output, generated help/docs, automation consumers, or a changed-interface-to-validation map. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for pure routing or trivial wording work where the output contract and quality gate are enough.

# Output Contract

Return a CLI/TUI/daemon interface design with:

- `mode_selected`: command contract, machine output compatibility, destructive/operator action, daemon lifecycle, or TUI/interactive flow
- `interface_evidence`: current commands, generated help, docs, tests, scripts, service units, config files, automation consumers, repository graph, project memory, execution trajectory, and freshness limits inspected
- `graph_memory_trajectory_judgment`: graph, memory, and trajectory evidence accepted, rejected, or not verified, with current-source confirmation
- `command_model`: commands, subcommands, positional args, flags, aliases, hidden/deprecated commands, stability tier (stable/beta/experimental)
- `config_precedence`: ordered list of defaults, config files, env vars, flags, secrets, profile selection
- `output_contract`: stdout format per command, stderr diagnostics format, machine-readable mode schema reference, stability guarantee window
- `exit_codes`: numeric table with meaning, retry guidance, and signal mapping
- `safety_controls`: dry-run behavior, confirmation strategy, target scoping flags, idempotency keys, lock and temp-file ownership
- `signal_lifecycle`: `SIGINT` / `SIGTERM` / `SIGHUP` / `SIGUSR1` behavior, drain timeout, cleanup order
- `daemon_behavior`: start/stop/status/reload, readiness vs liveness, structured log schema, PID/lock path, supervision target (systemd/launchd/k8s)
- `tests`: golden output, exit-code matrix, config precedence, signal/drain, idempotency/rerun, dry-run honesty, TTY-vs-pipe behavior
- `documentation`: command help, examples for each command, deprecation notes with removal version, automation contract reference
- `changed_interface_to_validation_map`: each command, flag, config precedence, output schema, exit code, dry-run, signal, daemon, and TUI decision mapped to validation evidence or residual risk
- `handoff_boundaries`: what belongs to shell implementation, daemon internals, security/privacy, reliability/observability, delivery rollout, docs, or no-next-gate rationale
- `evidence_limits`: what was not verified, such as unknown external scripts, OS-specific supervisors, terminal emulators, production service managers, real signal timing, or hidden automation consumers

# Evidence Contract

Close a CLI/TUI/daemon interface design only when these answers are concrete:

- **Basis:** selected mode, interface owner, changed command/daemon/TUI boundary, compatibility tier, and why the interface decision is needed.
- **Boundaries inspected:** current commands, generated help, docs, tests, scripts, service units, config files, automation consumers, repository graph, project memory, execution trajectory, and skipped surfaces with reason.
- **Safety and compatibility:** command model, config precedence, stdout/stderr split, machine-output schema, exit-code taxonomy, destructive-action controls, daemon/TUI lifecycle when applicable, and security/privacy handoff.
- **Validation:** changed-interface-to-validation map, commands or artifacts, exit code/status, freshness after final edit, skipped coverage, and negative evidence.
- **What evidence proves:** the exact command, flag, output schema, exit code, dry-run, config, signal, daemon, or TUI behavior covered by each proof.
- **What evidence does not prove:** unknown external scripts, uninspected OS supervisors, production service managers, terminal emulators, hidden automation consumers, and real signal timing unless tested.
- **Closure:** handoff boundaries, rollback or compatibility note, residual risk, and next gate or owner.

A command list, help text, or "add --json" statement is not sufficient evidence.

# Benchmark Coverage

Improved interface designs should reject common weak patterns: human prose parsed by automation, progress on stdout, one exit code for every failure, `--force` as the only destructive guard, production defaults without scope, secrets in argv, daemon readiness before dependencies, reload that crashes on invalid config, lock files used as stale sentinels, and TUI prompts that hang non-TTY CI. Detailed matrices and examples belong in references so this body stays efficient.

# Routing Coverage

Route here when the primary work is command grammar, flag semantics, config precedence, machine output, stdout/stderr, exit-code taxonomy, dry-run, idempotent operator actions, daemon lifecycle, signal handling, TUI/non-TTY behavior, or scriptability. Hand off when the primary concern is shell implementation (`shell-cli-professional-usage`), generic runtime configuration (`configuration-runtime-policy`), release execution (`delivery-release-gate`), daemon internals or service code (`backend-change-builder`), observability readiness (`reliability-observability-gate`), security/privacy (`security-privacy-gate`), or output consumer compatibility (`consumer-impact-analysis`).

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
10. Repository graph, project memory, and execution trajectory inputs are current-source confirmed or marked not verified before they shape command behavior.
11. Every changed command, flag, output schema, exit code, dry-run, config, signal, daemon, or TUI decision maps to validation evidence or a named residual risk.
12. Handoff boundaries and evidence limits are explicit so interface design is not over-claimed as shell implementation, security approval, release readiness, or production observability.

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
