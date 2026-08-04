# CLI Daemon Interface Design Benchmarks And Patterns

Load this reference when command grammar, machine output, exit/retry semantics, destructive operation safety, daemon lifecycle, reload, or TTY behavior changes. Do not load it for internal library APIs or shell implementation details with no interface-contract change.

## Interface Mode

| Mode | Contract to preserve | Required proof |
| --- | --- | --- |
| Human one-shot | Discoverable grammar/help and recoverable diagnostics. | Help/examples, invalid arguments, target/context display, and exit behavior. |
| Automation command | Stable structured/porcelain output and classified failure. | Schema/golden plus a real parser/consumer fixture with stderr separated. |
| Destructive operator tool | Explicit target, preview/no-write boundary, confirmation or policy gate, idempotent status/repair. | Wrong-target rejection, no-mutation preview, partial rerun, audit, rollback/compensation. |
| Stream | Record framing/schema, ordering, partial-output, backpressure, and cancel behavior. | For the bounded stream fixture or test run, parse each emitted record and exercise interruption or terminal behavior; disclose untested record variants, production volume, and backpressure. |
| Daemon/service | Startup, readiness, liveness, reload, drain, signal, lock, child, and cleanup semantics. | Supervisor/platform config plus relevant lifecycle/signal tests. |
| TUI/wizard | Keyboard/cancel/resize/terminal restoration and a non-interactive contract. | TTY and non-TTY/CI behavior without a hanging prompt. |

## Output, Errors, And Compatibility

In a declared machine-readable mode, reserve stdout for bytes that conform to its valid schema.
Route diagnostics, prompts, warnings, progress, and logs to stderr.
Human output may evolve unless promised stable.
Define additive, breaking, and deprecation rules for structured or porcelain consumers.
Version that contract when necessary.
Inventory current scripts, CI, cron, docs, and external users.

Define exit classes from caller recovery needs.
Cover success, usage or input, validation or precondition, partial or unknown outcome, transient dependency, timeout or cancellation, and internal failure.
Use platform-standard signal conventions where applicable.
Do not impose a universal custom numeric table.
Publish exact codes in this command’s contract.
Test the published retry guidance.

Destructive or non-local commands share discovery and validation between preview and execution, then stop before the mutation adapter. Bind target/profile/tenant/cluster, reject ambiguous production defaults, protect secrets from argv/help/logs, and define lock/idempotency/checkpoint/status/repair for partial reruns. When a preview skips remote validation, state the resulting proof limits.

## Daemon, Config, And Terminal Failure

Report ready only after the listener and required dependencies satisfy the current readiness contract; keep liveness distinct. On shutdown, stop intake, bound drain, flush owned state/telemetry, forward/reap children where applicable, and release locks. Parse and validate a complete reload before atomic apply; keep the last good state on rejection. Use an actual platform lock primitive when mutual exclusion matters; PID files are diagnostic unless the platform proves otherwise.

Config precedence is an explicit product/platform contract, not a universal default. Secrets use an approved environment/file/stdin/keychain/secret-store path that avoids process-list and shell-history exposure. When a command may run interactively or mutate terminal state, detect the relevant input and diagnostic TTYs. Define supported non-interactive behavior, restore changed terminal state on exit paths, and follow current color and accessibility conventions.

## Evidence And Proof Limits

Inspect current command tree, help/docs, output consumers, scripts, service units/manifests, config, and tests. Repository search cannot enumerate private external scripts. Local signal or readiness tests do not prove complete supervisor, OS, or container coverage. Golden output does not prove semantic compatibility. A no-write preview does not prove external permissions or quota unless exercised.

Reject human tables parsed as an undeclared API, progress on machine stdout, retry-ambiguous failures, `--force` as the sole target guard, and secrets in arguments. Also reject premature readiness, partial invalid reload, PID-file-only locking, and prompts that hang non-TTY execution.

Route shell mechanics to `shell-cli-professional-usage` and config lifecycle to `configuration-runtime-policy`.
Route output consumers to `contract-testing` or `consumer-impact-analysis`.
Route secrets or privilege to `security-privacy-gate` and daemon operations to `reliability-observability-gate`.
Route production mutation or release commands to `delivery-release-gate`.
