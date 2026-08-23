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

After `quality-test-gate` defines strategy/acceptance, select repository commands/coverage; record freshness facts while Core Guard G owns timing.

## Inputs

- accepted proof strategy, acceptance, changed paths, risks, repository entrypoints/tests, execution constraints, and available freshness facts.

## High-Value Rules

- Map acceptance and risk to the smallest-sufficient evidenced commands and coverage.
- Record target, directory, effects, authority, stop, recovery, cleanup, and retained output before execution.
- Record the result and freshness facts.
- Select a repository fallback only from coverage evidence.
- Preserve unsupported coverage, proof limits, and residual risk.

## Anti-Patterns

- Local success substituted for evidence of the targeted validation selection contract.

## Stop Conditions

- Stop without evidenced coverage, resolved execution boundaries, or authority.
- Do not invent entrypoints, fallbacks, coverage, or timing.

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
