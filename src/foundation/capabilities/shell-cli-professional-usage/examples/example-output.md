# Example Output

```markdown
## Shell Review

Safety: Uses `set -euo pipefail` and quoted variables.
Targets: Refuses to run unless target directory contains expected marker file.
Output: JSON summary on stdout; diagnostics on stderr.
Rerun: Idempotent after partial copy failure.
Decision: Accept after ShellCheck and dry-run test.
```
