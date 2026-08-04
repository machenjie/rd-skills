# Shell CLI Professional Usage Checklist

- Use compatible safety options such as `set -euo pipefail`.
- Quote variables and review globbing behavior.
- Use safe temp files and cleanup traps.
- Validate destructive targets and provide dry-run where possible.
- For an accepted automation consumer, keep stable machine data on stdout and diagnostics on stderr.
- Verify the shell returns the accepted exit semantics for success, expected absence, partial failure, and invalid use.
- Prove idempotency or add safeguards for non-idempotent operations.
- Run ShellCheck or equivalent review where applicable.
