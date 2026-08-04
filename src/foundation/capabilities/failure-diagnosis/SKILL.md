---
name: failure-diagnosis
description: "`analysis-agent`/`task-agent`/`review-agent`: use when symptoms, logs, metrics, regressions, or incidents need cause analysis; skip when no diagnosis decision exists."
---

# failure-diagnosis

## Registry Trigger

**Use when**

- diagnose failures SEV incident response symptoms logs metrics regressions hypotheses root cause and postmortem actions

**Do not use when**

- no task-local failure diagnosis decision is required

## Skill Role

Bound symptoms, calibrate hypotheses, establish reproduction or equivalent causal proof, state proof limits, and justify corrective action without claiming downstream ownership.

## High-Value Rules

- **Bound the observed failure before explaining it.** Record affected behavior, impact, onset, scope, healthy comparison, and current evidence provenance; distinguish missing evidence from evidence of absence.
- **Use hypotheses to choose discriminating observations.** Derive predictions from each plausible mechanism, seek both supporting and counter-evidence, and update confidence when observations conflict instead of searching only for confirmation.
- **Separate symptom, trigger, mechanism, root cause, and contributors.** Accept a root-cause claim only when it explains the observed boundary and a counterfactual change would prevent or materially contain recurrence.
- **Prefer controlled reproduction without making it universal.** When reproduction is unsafe, unstable, destructive, or environment-specific, require a coherent causal evidence chain, alternative explanations considered, and explicit proof limits.
- **Scale diagnostic structure to ambiguity and consequence.** Track competing hypotheses and elimination evidence when several mechanisms remain credible; a dedicated table is optional unless the task or incident policy requires it.
- **Require a credible causal boundary before correction.** The smallest correction closes the verified mechanism, includes its regression oracle, and stays separate from broader improvement.
- **Preserve uncertainty and freshness.** Tie claims to timestamps, versions, topology, configuration, and source identity; leave unresolved paths, stale evidence, and externally owned mechanisms with accountable next evidence.

## Anti-Patterns

- Stop at a deployment, request, operator action, or other trigger without explaining the enabling system condition.
- Treat correlation, a single successful retry, one familiar failure mode, or absence from sampled logs as causal proof.
- Declare a cause after the fix appears to work while the failure mechanism, counterfactual, and residual uncertainty remain untested.

## Stop Conditions

Escalate financial, safety, security, privacy, regulatory, destructive-data, conflicting-evidence, or harmful-observation consequences under current incident policy. Also escalate unavailable production evidence, unresolved authority, or risk without an accountable owner.

## Output Contract

- bounded diagnosis with symptoms, timeline, evidence provenance, causal hypotheses, discriminating observations, verified or provisional cause, reproduction or equivalent proof, corrective rationale, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | A real symptom needs competing hypotheses or causal reconstruction | The verified failure mechanism is already established | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Diagnosis spans triggers, contributors, timelines, and falsifying checks | No unresolved symptom or causal question remains | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence freshness](references/evidence-freshness.md) | evidence-pattern | Cause claims depend on current logs, traces, commands, or source | No diagnostic conclusion awaits freshness review | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
