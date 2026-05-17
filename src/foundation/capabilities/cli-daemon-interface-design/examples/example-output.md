# Example Output

```markdown
## CLI Interface Design

Command: changeforge deploy apply

Config precedence:
- defaults < config file < environment < flags
- `--profile` is required for production.

Output:
- stdout: JSON when `--output json` is set.
- stderr: progress, warnings, and validation errors.

Exit codes:
- 0 success
- 2 invalid arguments
- 10 validation failed
- 20 deployment rejected by remote API
- 130 interrupted by SIGINT

Safety:
- `--dry-run` prints planned changes and performs no writes.
- Production requires `--target production --confirm production`.

Tests:
- Golden JSON output, config precedence, dry-run no-write, and SIGTERM cleanup.
```
