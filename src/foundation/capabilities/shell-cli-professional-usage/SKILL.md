---
name: shell-cli-professional-usage
description: Use when writing or reviewing Shell scripts, CLI tools, and operational commands with focus on idempotency, quoting, exit codes, pipefail, temp files, destructive command safety, stdout and stderr contracts, logging, dry-run behavior, and rerun safety.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "95"
changeforge_version: 0.1.0
---

# Mission

Enforce professional Shell / CLI / operational-tool usage: strict shell options, robust quoting, safe temp files, meaningful exit codes, `--dry-run` for destructive operations, clear stdout/stderr contract, structured logging to stderr, idempotency, and explicit target validation. Treat operational scripts as production code with the same review, test, and rollback discipline as application code — because they often run as root, on production, with no UI to confirm intent.

# Pinned Tooling Baseline (Shell / CLI)

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- **Shell**: Bash ≥ 4.4 (5.x preferred for `mapfile`, `${var,,}` lowercasing, robust `[[ -v ]]`); explicit `#!/usr/bin/env bash` shebang and `set -euo pipefail`. **POSIX `sh`** only when explicitly required (Alpine / busybox / Dockerfile RUN with `sh`); document the constraint.
- **Linter**: **ShellCheck** ≥ 0.10 (`shellcheck -S warning script.sh`), run in CI on every shell file. Findings either fixed or annotated inline (`# shellcheck disable=SCxxxx # reason: ...`).
- **Formatter**: `shfmt` ≥ 3.8 with project config (e.g., `shfmt -i 2 -bn -ci -sr`); CI runs `shfmt -d`.
- **Test framework**: `bats-core` ≥ 1.11 for unit + integration tests of shell logic. Hermetic tests via `mktemp` directories.
- **Static analysis (extra)**: `bashate` for style; `checkmake` for Makefiles; `hadolint` for Dockerfiles.
- **Cross-platform CLI alternatives**: where the script grows beyond ~200 lines or needs portable error handling / argument parsing / structured output, **rewrite in Python / Go / Rust**. Shell is for orchestration, not application logic.
- **CLI argument parsing**: prefer GNU-style long options (`--target=...`) with short equivalents; use `getopts` (POSIX, short only) or `getopt` (GNU long-opt) carefully; for any non-trivial CLI, move to Python (`argparse` / `click`) or Go (`cobra` / `urfave/cli`) or Rust (`clap`).
- **Logging**: structured to **stderr** (JSON if consumed by log pipeline; plain otherwise). **stdout is for machine-readable data output only.**

# When To Use

Use when shell scripts, CLI commands, install / release / rollback scripts, CI steps, migration helpers, operational tools, or destructive command wrappers are added or changed. Use whenever a script will run on a production host, in CI, as a release step, or with elevated privileges.

# Do Not Use When

Do not use to bless ad-hoc commands as permanent automation without dry-run, idempotency, target validation, and tests. Do not use to teach shell syntax.

# Stage Fit

Launched in coding, bug-fix, code-review, refactoring, and testing. Per-stage focus:

- **coding**: `set -euo pipefail`, quoting, injection-safe argument passing, idempotency, exit codes.
- **debugging-diagnosis**: word-splitting/globbing bugs, unset-variable failures, non-portable constructs, silent pipe failure.
- **code-review**: unquoted expansion, `eval` and command injection, missing target validation, destructive `rm` safety.
- **refactoring**: function extraction, `shellcheck`-clean rewrite, POSIX vs bash portability.
- **testing**: dry-run and `bats`, idempotency re-run, target-validation tests.

# Non-Negotiable Rules

- **Strict-mode header** at the top of every Bash script: `set -euo pipefail` + (optional) `IFS=$'\n\t'`. Failure exits the script; unset variables are errors; pipeline failures propagate.
- **Quote every variable expansion**: `"$var"`, `"${array[@]}"`, `"$@"`. Unquoted expansions are word-split and glob-expanded — a known security and correctness failure mode (CWE-78 OS command injection).
- **`mktemp` for temp files**: `tmp=$(mktemp -t mytool.XXXXXX)`; never `/tmp/predictable_name.$$`. Clean up via `trap`.
- **`trap` for cleanup**: `trap 'rm -rf -- "$tmp"; exit' EXIT INT TERM HUP`. Cleanup is paired with resource creation.
- **Destructive operations require `--dry-run` and target validation.** `rm -rf` / `DROP TABLE` / `kubectl delete` / `aws rds delete-db-instance` wrappers must:
  1. Default to dry-run mode unless `--apply` / `--yes` is explicitly given.
  2. Validate the target (regex, allowlist, environment guard — e.g., `if [[ "$ENV" == "prod" && "$CONFIRM" != "DESTROY_PROD" ]]; then exit 1; fi`).
  3. Echo the exact command they will run before running it.
  4. Require interactive confirmation (or `--yes` flag) for production scope.
- **`stdout` is data; `stderr` is diagnostics.** CI / pipelines parse stdout. Logs, progress, prompts go to stderr (`>&2`). Mixing breaks downstream consumers.
- **Exit codes are meaningful and documented**: 0 success, 1 generic error, 2 misuse / bad args, 3-125 application-specific (documented), 126 not executable, 127 not found, 128+N killed by signal N, 130 SIGINT. Document the script's exit-code table.
- **Idempotent or explicitly non-idempotent**: re-running the script after partial failure either does the right thing (idempotent: check-then-act) or fails fast with a clear message. Use checksums, lock files, `INSERT ... ON CONFLICT`, `kubectl apply` (idempotent) over `kubectl create` (not).
- **Secrets are never on the command line** (visible in `ps`). Pass via env var, file, or stdin pipe. Never echo secrets; never `set -x` while a secret is in scope.
- **Subprocess composition uses arrays, not strings**: `cmd=(rsync -a "$src/" "$dst/"); "${cmd[@]}"` — not `cmd="rsync -a $src/ $dst/"; $cmd`.
- **No `eval` on attacker-controllable input.** `eval` of untrusted data is RCE. `bash -c "$user_input"` is the same bug.
- **`find ... -exec`**: prefer `-exec ... +` (batches) over `-exec ... \;` (per-file fork); for non-trivial transforms use `find -print0 | xargs -0 -n1 ...` to handle filenames with whitespace / newlines.

# Industry Benchmarks

- **POSIX.1-2017 shell standard** and **Bash Reference Manual**.
- **Google Shell Style Guide**.
- **ShellCheck wiki** — each SC#### rule documents a real bug class.
- **CWE Top 25** — CWE-78 (OS command injection), CWE-22 (path traversal), CWE-377 (insecure temp file), CWE-269 (improper privilege management), CWE-732 (incorrect permissions).
- **Twelve-Factor App** — config from env, logs to stdout/stderr, processes are stateless.
- **CLI design**: **"Command Line Interface Guidelines"** (clig.dev), **GNU coding standards** for argument conventions (`--help`, `--version`, `--quiet`, `--verbose`).
- **`set -euo pipefail` caveats** (Aaron Maxwell, "Unofficial Bash Strict Mode") — known edge cases with `set -e` (e.g., inside `if`, `&&`, `||`).
- **Operational runbook practice** — idempotency, dry-run, rollback as first-class.

# Selection Rules

Select when shell, CLI, scripts, CI commands, release commands, destructive operations, stdout/stderr contracts, or rerun safety appear. Pair with `delivery-release-gate` (release / rollback scripts), `security-privacy-gate` (secrets, injection), `quality-test-gate` (bats tests), `cli-daemon-interface-design` (broader CLI contract design).

# Proactive Professional Triggers

- **Signal:** a shell command, flag, pipeline, release helper, or CI step is copied from project memory, old docs, terminal history, or prior execution without reading the current script/help/tests/callers. **Hidden risk:** stale command shape, deprecated flag, wrong working directory, or changed output contract is encoded into automation. **Required professional action:** inspect current source and consumers before accepting the command. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, command/help output, accepted/rejected memory, consumer list, and freshness limit.
- **Signal:** `rm`, `find -delete`, `kubectl delete`, `aws * delete`, `DROP`, `terraform apply`, migration, release, rollback, or production-target command lacks default dry-run, scoped selector, confirmation token, and rollback note. **Hidden risk:** one mistyped environment, glob, context, or rerun mutates or deletes the wrong target. **Required professional action:** require dry-run proof, target validation, explicit apply flag, and rerun/rollback behavior before closure. **Route to:** `delivery-release-gate`, `agent-tool-permission-sandbox`, `quality-test-gate`. **Evidence required:** dry-run output, target guard test, command exit code, rollback path, and residual destructive risk.
- **Signal:** command output is piped, parsed by CI, consumed by another script, or documented as machine-readable while progress, warnings, prompts, or logs may reach stdout. **Hidden risk:** automation silently parses human text, drops records, or treats diagnostics as data. **Required professional action:** define stdout/stderr contract and add parse/golden-output validation. **Route to:** `cli-daemon-interface-design`, `contract-testing`, `consumer-impact-analysis`. **Evidence required:** stdout schema, stderr diagnostic sample, pipe test command, golden output diff, and compatibility window.
- **Signal:** secret, token, password, kube context, cloud profile, SSH key, private URL, or bearer credential appears in argv, shell history, `set -x`, logs, temp files, or generated reports. **Hidden risk:** credentials leak through process lists, CI logs, terminal transcripts, or retained evidence. **Required professional action:** move secrets to env/file/stdin, disable tracing around secret scope, redact output, and classify tool permission/sandbox. **Route to:** `security-privacy-gate`, `secret-configuration-security`, `agent-tool-permission-sandbox`. **Evidence required:** no-secret-in-argv review, redacted log sample, secret-scan output, and retention boundary.
- **Signal:** filenames, paths, globs, `find`/`xargs`, temp files, locks, loops, or rerun state depend on external input without null delimiters, quoting, `mktemp`, `trap`, `flock`, or idempotency checks. **Hidden risk:** whitespace/newline names, TOCTOU, parallel runs, or partial failures corrupt data even when ShellCheck is green. **Required professional action:** validate path handling, cleanup, locking, and rerun semantics with hostile fixtures. **Route to:** `quality-test-gate`, `input-validation`, `concurrency-control`. **Evidence required:** hostile filename fixture, cleanup/trap proof, lock/rerun test, ShellCheck output, and untested OS/filesystem limit.

# Risk Escalation Rules

- Escalate to `delivery-release-gate` for any script run as part of release / rollback / production operations.
- Escalate to `security-privacy-gate` for secrets handling, command injection risk, `eval` of external input, or elevated-privilege execution.
- Escalate to `quality-test-gate` for bats / dry-run / chaos test evidence.
- Escalate to `cli-daemon-interface-design` for non-trivial CLI contract design (subcommand structure, machine-readable output, `--json` mode).
- Escalate to `language-runtime-selection` when the script crosses ~200 lines or grows error-handling / data-structure complexity (rewrite as Python / Go / Rust).

# Critical Details

- **`set -e` edge cases**: does not trigger inside `if`, `while`, `until`, `&&`, `||`, function bodies in subshells, or commands prefixed with `!`. Test the failure path; don't assume `set -e` catches everything.
- **`set -o pipefail`** makes pipeline exit code = rightmost non-zero (instead of last command's). Required for `grep | head` style pipelines to detect grep failure.
- **Unquoted expansion bugs**: `rm $file` where `file="a b.txt"` becomes `rm a b.txt` (two files). `for f in $files` word-splits. Always quote.
- **`[[ ]]` over `[ ]`** in Bash (no word-splitting inside; supports `=~` regex, `&&`, `||`); `[[ $x = pattern ]]` for glob match; `[[ $x =~ ^[0-9]+$ ]]` for regex.
- **`$()` over backticks** for command substitution (nests cleanly).
- **Arrays** for collections: `args=(--verbose --output "$file"); cmd "${args[@]}"`. Strings split unpredictably.
- **`local`** in functions: declare every function-local variable as `local` to avoid leaking to caller scope. `local -r` for read-only.
- **`readonly` / `declare -r`** for constants at script top.
- **Process substitution `<(cmd)`** for passing command output as a file: `diff <(cmd1) <(cmd2)`.
- **`getopts` (POSIX, short options only)** for portable arg parsing; `getopt` (GNU) for long options but requires version check (`getopt --test`). Beyond trivial: move to a real language.
- **Locale / `LC_ALL=C`** for deterministic sort / comparison: `LC_ALL=C sort` avoids locale-dependent collation surprises.
- **`set -x`** for debugging — turns on tracing; turn off (`set +x`) before secrets enter scope. Never leave `set -x` in production scripts.
- **Heredocs**: `<<-EOF` strips leading tabs (only tabs, not spaces); `<<'EOF'` (quoted) suppresses variable expansion — use for embedded SQL / YAML / scripts that must be literal.
- **Race conditions on shared state**: `flock` for file-based locking; never "check if exists, then act" without locking (TOCTOU bug class).
- **`curl` / `wget` for downloads**: `curl --fail --silent --show-error --location -o file url` — default behavior of these tools is to silently succeed on HTTP errors and follow redirects.
- **`set -u` and `"${1:-default}"`** — with strict unset-var detection, use `${var:-default}` or `${var-}` to provide defaults without tripping `-u`.
- **PATH safety**: in security-sensitive scripts, set `PATH` explicitly (`PATH=/usr/sbin:/usr/bin:/sbin:/bin`); never trust inherited PATH for root scripts.
- **`umask`**: set explicitly when creating files that should not be world-readable (`umask 077`); `mktemp` already creates with mode 0600.

# Failure Modes

- **Unquoted variable globbing** — Symptom: `rm $tmp_dir/*` deletes wrong files when var has whitespace or is empty (then deletes `/*`). Cause: missing quotes / no `:-` default. Detection: ShellCheck SC2086. Impact: data loss.
- **Predictable temp file** — Symptom: race-condition exploit / TOCTOU. Cause: `/tmp/foo.$$` instead of `mktemp`. Detection: ShellCheck SC2086, SC2188 plus review. Impact: CVE-class (CWE-377).
- **`set -e` false sense of safety** — Symptom: script continues after failure that `set -e` should have caught. Cause: failure inside `if` / pipe / function-in-subshell. Detection: explicit error check + tests. Impact: half-finished operations.
- **stdout/stderr mixed** — Symptom: CI parser breaks; "[info] starting..." parsed as data. Cause: progress to stdout. Detection: review + CI contract test. Impact: pipeline breakage.
- **Destructive without dry-run** — Symptom: production data dropped on accidental invocation. Cause: no `--dry-run` default; no target validation. Detection: code review + bats test. Impact: outage / data loss.
- **Non-idempotent rerun** — Symptom: rerun after partial failure doubles state or fails confusingly. Cause: `CREATE` instead of `apply`; no idempotency key. Detection: chaos rerun test. Impact: corrupted state.
- **Secret on command line** — Symptom: secret visible in `ps`, process tree, kernel audit log. Cause: `tool --password $SECRET`. Detection: review + secret-scanning. Impact: credential exposure.
- **`eval` on user input** — Symptom: arbitrary command execution. Cause: `eval "$user_cmd"`. Detection: ShellCheck SC2294, code review. Impact: RCE.
- **PATH hijack** — Symptom: root script runs attacker-controlled binary. Cause: inherited writable PATH entry. Detection: explicit PATH set; review. Impact: privilege escalation.
- **TOCTOU race on shared file** — Symptom: two concurrent invocations corrupt state. Cause: "check then act" without `flock`. Detection: `flock` mandate; chaos test. Impact: corruption.
- **`curl | bash`** — Symptom: arbitrary script executed from network. Cause: install pattern unverified. Detection: prefer pinned artifacts + checksum; document risk. Impact: supply-chain compromise.
- **Script grew to 1000 lines** — Symptom: error handling fragile; tests painful; data structures awkward. Cause: shell beyond its sweet spot. Detection: line-count + complexity review. Impact: bugs, hard to maintain.

# Reference Loading Policy

Read `references/checklist.md` when shell/CLI changes touch file deletion, quoting, globbing, `eval`, secrets, temp files, idempotent reruns, dry-run behavior, portability, traps, stdout/stderr, or exit-code contract. Use `examples/example-output.md` only when the expected Shell / CLI Usage Review shape is unclear. Do not load either file for comment-only script edits.

# Output Contract

Return a **Shell / CLI Usage Review** containing:
- **Shell + version** required; portability target (POSIX / Bash 4 / Bash 5)
- **Tooling pins**: shellcheck + shfmt + bats versions; CI invocation commands
- **Safety options**: `set -euo pipefail`, IFS, PATH, umask choices
- **Quoting audit**: every variable expansion quoted; arrays for command composition
- **Temp file discipline**: `mktemp` + `trap` cleanup
- **Target validation**: env-guard, allowlist, regex; what prevents this from running against prod by accident
- **Dry-run mode**: default-on for destructive; `--apply` / `--yes` to commit; sample dry-run output
- **stdout/stderr contract**: which is which; example for pipeline consumer
- **Exit codes table**: each used code documented
- **Idempotency**: rerun-safety mechanism (lock / upsert / checksum / `apply`)
- **Secrets handling**: env vars / files / stdin; never on command line; `set -x` boundaries
- **Logging**: structured (where consumed by log pipeline) or plain to stderr
- **Tests**: bats coverage of success, failure, dry-run, rerun, target-validation-block paths
- **Accepted exceptions** with owner / scope / expiration

# Evidence Contract

A shell/CLI change is professionally complete only when the output includes:

- **Execution safety**: `set -euo pipefail` decision, trap cleanup, exit codes, and failure propagation.
- **Quoting/injection boundary**: variables quoted, arrays used for arguments, no unsafe `eval`, no glob surprises.
- **Idempotency**: repeated run behavior, partial failure recovery, temp file cleanup, and dry-run support when applicable.
- **Portability**: bash vs POSIX shell, OS assumptions, required tools, and version checks.
- **Secret safety**: no secrets echoed, logged, or passed through process list unsafely.
- **Validation evidence**: shellcheck, bats/shunit test, dry-run output, or not-verified disclosure.
- **What evidence proves**: the inspected shell interface and execution safety risk is covered.
- **What evidence does not prove**: every OS distribution, production filesystem state, or external command behavior.
- **Residual risk**: untested runtime behavior, owner, and next gate.

# Quality Gate

1. ShellCheck (severity ≥ warning) green; shfmt diff clean; bats tests pass.
2. `set -euo pipefail` present; PATH set explicitly for elevated-priv scripts; umask reasonable.
3. All variable expansions quoted; arrays used for command composition.
4. Temp files via `mktemp` with `trap` cleanup.
5. Destructive operations default to dry-run; target validation present; production scope requires explicit confirmation.
6. stdout/stderr contract clear; consumers' parsing verified.
7. Exit codes documented and meaningful.
8. Idempotency mechanism present, or non-idempotency clearly flagged with safeguards.
9. No secrets on command line; no `eval` of external input; no `curl | bash` install without checksum.
10. Script length / complexity within shell's sweet spot (~200 lines floor); if larger, migration plan to Python / Go / Rust documented.

# Used By

delivery-release-gate, ci-cd, project-initialization, quality-test-gate, ai-code-review-refactor, cli-daemon-interface-design

# Handoff

- **`delivery-release-gate`** for release / rollback / production-operation scripts.
- **`security-privacy-gate`** for secrets, injection, elevated-privilege execution, command-injection risk.
- **`cli-daemon-interface-design`** for non-trivial CLI contract (subcommands, machine-readable output, daemonization).
- **`quality-test-gate`** for bats / dry-run / chaos test evidence.
- **`language-runtime-selection`** when the script outgrows shell and should be rewritten.

# Completion Criteria

Review is complete when: shellcheck + shfmt + bats are green; strict-mode + quoting + temp-file discipline is in place; destructive operations have dry-run + target validation + confirmation; stdout/stderr contract is explicit; exit codes are documented; idempotency is designed; secrets stay off the command line; and any accepted exception has owner, scope, and expiration. Scripts that have grown beyond shell's sweet spot have a documented migration plan to a real programming language.
