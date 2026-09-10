# Diagnostic Evidence Freshness

Use this reference when a diagnosis depends on repository inspection, prior task evidence, generated reports, prior command output, validation freshness, or observable action sequence. Bind each item to the claim and event window it can support. Historical incident evidence can establish cause when its source, event time, affected version, and configuration are known; current-state and repair claims require current supporting evidence.

## Freshness Decision

- **Current evidence:** matches the source, configuration, and event window of the claim. For current-state or repair claims, use evidence after the final relevant material change; for historical cause, inspect the incident version and contemporaneous records.
- **Selector-only evidence:** useful for choosing files, hypotheses, or commands, but not enough to prove cause or closure without current confirmation.
- **Stale evidence:** no longer matches the state or event window asserted by the claim. A later rollout or mitigation does not invalidate correctly bound evidence of the earlier failure; it does invalidate unsupported reuse as proof of the repaired current state.
- **Rejected evidence:** conflicts with stronger evidence for the same claim and event window; preserve the contradiction and record why that claim was rejected. Different historical and current states are not themselves a contradiction.

## Current Evidence And Freshness

- **Repository inspection:** use call edges, ownership, generated-file boundaries, tests, configurations, and registry links to select diagnostic scope.
- Verify current blast-radius edges against current files.
- Verify causal edges against the incident version and configuration, recording what changed since the event.
- **Prior task evidence:** list each remembered claim, source, available date or commit, validation anchor, and accepted or rejected decision.
- Never let memory override source or operational evidence bound to the claimed event window.
- **Observable action sequence:** preserve failed command, working directory, exit code, output signature, attempted fix, and learned fact.
- After two same-path failures, choose a new hypothesis or return a concrete blocker.
- **Validation freshness:** after a material code, config, fixture, dependency, generated-artifact, or command-path change, rerun validation for affected current-state claims. Retain prior results as evidence of their original inputs, not of the repaired state.

## Closure Record

For any freshness-sensitive diagnosis, include:

- evidence source and timestamp or command path
- latest relevant change compared against that evidence
- current-source read or operational query used to reconcile it
- accepted, selector-only, stale, and rejected claims
- validator command, exit code, artifact/report path, and what it proves
- residual risk where current evidence cannot reproduce the original failure
