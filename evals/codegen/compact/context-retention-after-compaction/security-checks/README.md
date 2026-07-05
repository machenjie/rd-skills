# Security Checks

## Threat Surface

Verifies that compacted context evidence does not persist raw prompt, environment, secrets, full command output, full diff body, full file contents, or local absolute paths.

## Required Checks

- Bounded compaction evidence must not include raw prompts, raw command output, environment variables, secrets, full diff body, full file contents, or local absolute paths.
- Candidate artifacts must remain small and machine-inspectable.

## Rejection Cases

- Any raw prompt, raw command output, environment variable, secret, API key, full diff body, full file content, or local absolute path appears in submitted artifacts.
- Compaction evidence is unbounded or only self-reported in markdown.

## Expected Commands

- `bash ../security-checks/run.sh`
