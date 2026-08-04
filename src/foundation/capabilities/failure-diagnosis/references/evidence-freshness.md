# Diagnostic Evidence Freshness

Use this reference when a diagnosis depends on repository inspection, prior task evidence, generated reports, prior command output, validation freshness, or observable action sequence. Treat those signals as selectors until reconciled with current source and post-edit validation.

## Freshness Decision

- **Current evidence:** read from the current source, config, fixture, dependency lockfile, generated artifact, command output, metric, trace, or log after the latest relevant change.
- **Selector-only evidence:** useful for choosing files, hypotheses, or commands, but not enough to prove cause or closure without current confirmation.
- **Stale evidence:** older than the latest relevant code, config, fixture, dependency, generated report, command path, rollout, or mitigation change.
- **Rejected evidence:** contradicts current source, fresh command output, or stronger operational data; record why it was rejected so it is not reused later.

## Current Evidence And Freshness

- **Repository inspection:** use call edges, ownership, generated-file boundaries, tests, configurations, and registry links to select diagnostic scope.
- Verify candidate edges against current files before any blast-radius or cause claim.
- **Prior task evidence:** list each remembered claim, source, available date or commit, validation anchor, and accepted or rejected decision.
- Never let memory override current source or fresh operational evidence.
- **Observable action sequence:** preserve failed command, working directory, exit code, output signature, attempted fix, and learned fact.
- After two same-path failures, choose a new hypothesis or return a concrete blocker.
- **Validation freshness:** after a code, config, fixture, dependency, generated-artifact, or command-path change, rerun the relevant validator or downgrade previous green output to selector-only.

## Closure Record

For any freshness-sensitive diagnosis, include:

- evidence source and timestamp or command path
- latest relevant change compared against that evidence
- current-source read or operational query used to reconcile it
- accepted, selector-only, stale, and rejected claims
- validator command, exit code, artifact/report path, and what it proves
- residual risk where current evidence cannot reproduce the original failure
