---
name: targeted-validation-selection
description: "Select exact repository-defined validation commands and coverage after a proof strategy exists; use when entrypoint choice or coverage is unresolved."
---

# targeted-validation-selection

## Registry Trigger

**Use when**

- an accepted proof strategy needs exact repository-defined commands;
- several entrypoints or existing tests have competing coverage claims.

**Do not use when**

- `quality-test-gate` has not defined proof strategy and observable acceptance;
- exact commands and their acceptance and risk coverage are already established.

## Skill Role

After `quality-test-gate` defines proof strategy and acceptance, select repository-defined commands and coverage. Core Guard G and the validation-freshness contract govern evidence timing. Record freshness input/hash/time only as facts.

## Inputs

- accepted proof strategy and observable acceptance;
- changed paths and material risk surfaces;
- repository guidance, command definitions, and existing tests;
- command targets, mutation surfaces, hooks/subprocesses, credentials, external effects, authority, recovery, cleanup, and retained-output constraints;
- available command results and freshness input/hash/time facts.

## High-Value Rules

- Inspect repository guidance and command definitions for test/build/schema/lint/static/generator entrypoints.
- When entrypoint coverage is disputed, use existing tests to establish the behavior and paths covered by candidate entrypoints.
- For the accepted proof strategy, map its observable acceptance and material risk surfaces to command coverage and repository sources.
- Select exact smallest-sufficient commands with combined coverage for the accepted mapping and a defined expected signal per command.
- Run a selected command only after resolving its target, working directory, hooks/subprocesses, mutation surfaces, credentials, external effects, authority, stop condition, recovery, cleanup, and retained-output boundary.
- Record freshness input/hash/time facts without deciding evidence timing.
- Select an unavailable-entry fallback only from repository-defined commands with evidenced coverage.
- Preserve unverified scope, proof limits, and residual risk when coverage remains incomplete.

## Anti-Patterns

- An invented command replaces inspection of repository-defined entrypoints.
- A command name or broad suite is treated as command coverage without a mapped signal.
- Framework habit overrides current repository guidance and existing tests.
- A freshness fact is converted into a timing or refresh verdict.

## Stop Conditions

- Stop selection for a surface when no repository-defined entrypoint has evidenced coverage.
- Stop execution when a command's target, mutation or external-effect boundary, credentials, authority, recovery, or cleanup is unresolved.
- Keep a safely selected but unauthorized command unrun and record the missing execution authority.
- Record no unavailable-entry fallback when no supported repository command exists.
- Keep conflicting or incomplete coverage as unverified scope.

## Output Contract

- Repository-entrypoint inspection evidence covering test/build/schema/lint/static/generator entrypoints and existing tests.
- Record exact smallest-sufficient commands.
- Map observable-acceptance and risk-surface coverage per command.
- Record the expected signal.
- Record command target, working directory, mutation/external-effect classification, credentials/authority, stop condition, recovery, cleanup, and retained-output boundary before execution.
- Record the actual result when run.
- Record freshness input/hash/time facts.
- Record the unavailable-entry fallback.
- State unverified scope, proof limits, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [repository command entry evidence](references/repository-command-entry-evidence.md) | evidence-pattern | repository-defined entrypoints or existing tests have competing coverage claims | exact commands sources coverage signals and gaps are already recorded | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
