# Regression Testing Evidence Patterns

These records tie recurrence closure to the known mechanism, counterfactual proof, and reachable variants.

## Failure-Mechanism Claim

- Name the defect source, causal trigger, prior wrong observable result, affected boundary, and test path.
- Record the fixture or minimized-equivalent rationale, including state, role, ordering, timing, dependency behavior, redaction, and drift owner.
- Show that the selected level retains the causal mechanism; name real boundaries excluded by a narrower substitute.

## Counterfactual Claim

- For unfixed replay, record the protected revision or fault state, scoped command, matching failure, restoration path, and final fixed-state result.
- For mutation or fault challenge, record the reintroduced causal fault, guard failure, restored state, and what the challenge cannot reproduce.
- When counterfactual execution is unsafe or infeasible, record rejected options, reason, compensating proof or detection, owner, and revisit trigger.

## Recurrence Claim

- List same-pattern search scope and material matches across siblings, consumers, entry points, and duplicate implementations.
- Map each match to the new guard, another fresh guard, a corrected implementation, or explicit residual risk.
- For concurrency, record admissible and forbidden result sets plus scheduler or interleaving limits.
- For eventual consistency, record the semantic condition, observation bound source, final result, and timeout behavior.

## Freshness And Flake Limits

- Refresh evidence after material source, test, fixture, generator, schema, feature-flag, fake, environment, or validation-command changes.
- Preserve the first intermittent failure and record diagnostic reruns separately; quarantine records need owner, release consequence, and repair or removal trigger.
- Close with the known mechanism protected, variants unproved, automation limits, compensating detection, and next gate.
