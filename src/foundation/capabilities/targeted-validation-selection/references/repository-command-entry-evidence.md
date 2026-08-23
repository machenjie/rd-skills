# Repository Command Entry Evidence

Use this reference to compare repository-defined commands after proof strategy and observable acceptance are known.

- Inspect repository guidance and command definitions for test/build/schema/lint/static/generator entrypoints.
- Inspect test, build, schema, lint, static-analysis, and generator entrypoints defined by repository guidance or command configuration.
- Inspect existing tests for the paths and behavior exercised by each entrypoint.
- Record the exact source path and configuration key for every candidate command.
- Map each observable acceptance and risk surface to candidate command coverage.
- Select the smallest-sufficient commands whose combined coverage satisfies that mapping.
- Record each command's repository source, command coverage, and expected signal.
- Record the actual result when run and the associated freshness input/hash/time facts.
- Treat freshness values as facts; leave timing and refresh decisions to Core Guard G and the validation-freshness contract.
- When an entrypoint is unavailable, prefer a repository-defined fallback only when its coverage is evidenced.
- Record unavailable-entry fallback as none when no supported command exists.
- When gaps remain, preserve their unverified scope, proof limits, and residual risk.

## Anti-Patterns

- Reject invented commands, name-only coverage, framework-habit entrypoints, and freshness facts used as timing verdicts.
