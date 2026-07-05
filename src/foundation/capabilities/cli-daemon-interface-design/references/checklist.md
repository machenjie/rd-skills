# CLI Daemon Interface Design Checklist

- Define commands, subcommands, flags, positional arguments, aliases, and deprecated forms.
- Define config precedence across defaults, config files, environment variables, flags, and profiles.
- Reserve stdout for requested output and stderr for diagnostics.
- Provide stable machine-readable output when automation is expected.
- Define exit codes with remediation and retryability.
- Define dry-run, confirmation, target scoping, idempotency, locks, and temp-file cleanup.
- Define signal behavior for SIGINT, SIGTERM, and reload where applicable.
- Define daemon start, stop, status, readiness, health, logging, PID/lock, and shutdown semantics.
- Add tests for help, output, exit codes, config precedence, signal handling, and reruns.
