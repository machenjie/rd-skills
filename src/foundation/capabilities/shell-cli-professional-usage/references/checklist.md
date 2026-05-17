# Shell CLI Professional Usage Checklist

- Use compatible safety options such as `set -euo pipefail`.
- Quote variables and review globbing behavior.
- Use safe temp files and cleanup traps.
- Validate destructive targets and provide dry-run where possible.
- Keep stdout machine-readable and stderr diagnostic.
- Return meaningful exit codes.
- Prove idempotency or add safeguards for non-idempotent operations.
- Run ShellCheck or equivalent review where applicable.
