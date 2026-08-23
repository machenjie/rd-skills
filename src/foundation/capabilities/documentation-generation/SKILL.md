---
name: documentation-generation
description: "`task-agent`: change source-owned documentation; `review-agent`: assess documentation without mutation. Skip tasks requiring neither documentation change nor review."
---

# documentation-generation

## Registry Trigger

**Use when**

- task mode generates or updates README API docs ADR changelog runbook or migration notes
- review mode assesses documentation accuracy freshness or audience impact

**Do not use when**

- no task-local documentation generation decision is required
- an implementation diff has no separate documentation artifact

## Skill Role

Support source-grounded documentation work with an explicit role boundary.

- **Task mode (`task-agent`):** Produce the changed owning documentation source from current evidence.
- **Review mode (`review-agent`):** Return a documentation verdict and findings from non-mutating inspection.

## High-Value Rules

- Trace factual claims to current source, schemas, generated artifacts, tests, command output, accepted decisions, or release plans.
- Match depth to audience: operators need recovery actions, API consumers need semantics, contributors need validation, and users need impact.
- Classify deprecated, experimental, environment-specific, unverified, or inferred behavior explicitly in affected documentation.
- Update misleading documentation with behavior or record an owner and release consequence.
- Make examples executable, generated, or explicitly illustrative with proof limits.
- State compatibility, order, rollback, forward-fix, and ownership when versions diverge.

## Anti-Patterns

- Local success substituted for evidence of the documentation generation contract.

## Stop Conditions

Escalate public APIs, security posture, compliance, migrations, production configuration, incident procedures, release impact, or operator recovery. Stop for exposed secrets, source conflicts, unvalidated generation, or ownerless release documentation.

## Output Contract

- **Task mode (`task-agent`):** changed source-grounded documentation artifact; audience and behavior mapping; validation result; proof limits; residual documentation debt
- **Review mode (`review-agent`):** documentation verdict; severity-ranked findings; reviewed and unverified scope; proof limits; no mutation

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Source mapping, generation, command safety, or no-docs decisions need depth | A small wording fix has one current authoritative source | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Documentation changes APIs, migrations, operations, examples, or compatibility | No audience-facing behavior or procedure changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Documentation claims need fresh source, generator, or example validation | No factual or no-docs claim awaits proof | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
