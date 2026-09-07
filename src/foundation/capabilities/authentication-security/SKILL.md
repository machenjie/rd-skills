---
name: authentication-security
description: "Use with analysis-agent, task-agent, or review-agent for task-local authentication lifecycle and recovery risk. Do not use without that decision or as task owner."
---

# authentication-security

## Registry Trigger

**Use when**

- secure authentication sessions tokens passwords MFA and account recovery

**Do not use when**

- no task-local authentication security decision is required

## Skill Role

Own authentication lifecycle, recovery, linking, federation, and compromise.

## High-Value Rules

- Select controls from threat/provider/client/policy evidence.
- Define lifecycle, recovery/linking/federation, and compromise outcomes.
- Select one active named Reference.

## Anti-Patterns

- Local success is insufficient.

## Stop Conditions

- Stop on unclear controls, exceptions, or takeover risk.

## Output Contract

- authentication security review with controls failure cases and audits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Credential, session, federation, or recovery controls require mechanism selection | No authentication lifecycle or assurance boundary changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Affected flows include compromise, revocation, linking, or step-up denial | The change cannot issue, renew, recover, or revoke identity | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Authentication claims need fresh replay, fixation, or redaction proof | No lifecycle control claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
