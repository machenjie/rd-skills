# Shell CLI Benchmarks And Patterns

Use this reference after `cli-daemon-interface-design` supplies the applicable CLI representation and compatibility decision. Verify shell execution, portability, and evidence against that decision; route unresolved interface design back to its owner. Keep evidence mapping in `evidence-patterns.md`.

## Benchmark Anchors

- POSIX.1-2017 and Bash Reference Manual for shell semantics, portability limits, quoting, arrays, traps, and process behavior.
- Google Shell Style Guide and ShellCheck wiki for maintainable shell structure and bug-class-specific review.
- clig.dev and GNU command-line conventions for help/version flags, exit codes, stdin/stdout/stderr discipline, and machine-readable output.
- CWE-78, CWE-22, CWE-377, CWE-269, and CWE-732 for command injection, path traversal, insecure temp files, privilege, and file-permission risk.
- Operational runbook practice for dry-run, idempotency, rollback, stop conditions, and production command permission boundaries.

## Mode Pattern Matrix

| Mode | Strong pattern | Reject |
| --- | --- | --- |
| Destructive command | Shared argv array for dry-run/apply, scoped selector, explicit `--apply`, confirmation token, rollback note, target-guard test. | Preview string differs from applied command, implicit current kube/cloud context, or broad glob/delete without guard. |
| Automation output evidence | Accepted machine schema on stdout, diagnostics on stderr, accepted exit-code table, and parser/golden compatibility test. | Progress or warnings corrupt machine stdout, undocumented non-zero codes, or human text is parsed by automation. |
| Path/temp/rerun | Quoted arrays, null-delimited paths, `mktemp`, trap cleanup, `flock` when shared state exists, hostile filename fixture. | Predictable temp files, unquoted loops, newline-unsafe `xargs`, or ShellCheck as the only proof. |
| Secret-sensitive command | Secrets pass by env/file/stdin, tracing disabled before secret scope, redacted log sample, no raw values in retained artifacts. | Token in argv/history/logs, `set -x` around secrets, or post-run redaction as the main control. |
| Portability decision | POSIX constraint documented, Bash features version-gated, OS/tool assumptions checked, migration threshold named. | BusyBox/Alpine assumptions untested or Bash-only syntax in `sh` scripts. |

## CLI Compatibility Patterns

- Route non-trivial command grammar, help, configuration precedence, output schema/versioning, and exit-code design to `cli-daemon-interface-design`; retain shell execution checks as supporting evidence.
- Verify accepted help, flags, environment, configuration precedence, stdout/stderr, and exit semantics against current human and automation consumers.
- Verify the accepted compatibility window when flags, stdout fields, default targets, or exit codes change.
- Verify the accepted machine representation for automation consumers, with diagnostics kept outside its stdout payload.
- Use examples that run in tests or golden fixtures; docs-only command examples drift quickly.

## Shell Complexity Thresholds

- Keep shell for orchestration, file movement, environment setup, and small wrappers.
- Move to Python, Go, or Rust when code needs nested data structures, complex argument parsing, retries with state machines, JSON transformation, long-lived daemons, or broad cross-platform behavior.
- Treat roughly 200 lines as a review trigger, not an automatic rewrite. The decision depends on branching, testability, error handling, portability, and operator risk.

## Anti-Pattern Review Questions

- Does dry-run and apply share the same argv construction?
- Does the script work with spaces, newlines, globs, empty inputs, and missing arguments?
- Does a rerun after partial failure converge, fail fast, or double-apply?
- Does any command depend on inherited `PATH`, working directory, kube context, cloud profile, locale, or shell startup files?
- Are production operations guarded by explicit target validation and rollback/forward-fix evidence?
- Does any output, retained report, or terminal transcript contain credentials, private paths, or sensitive identifiers?
