---
name: security-privacy-gate
description: "Use `analysis-agent` to analyze permissions, secrets, sensitive data, trust boundaries, and injection; `task-agent` to implement controls; and `review-agent` to assess evidence. Skip self-review and no-trust-impact work."
---

# security-privacy-gate

## Role

- **Analysis mode (`analysis-agent`):** Trace paths.
- **Task mode (`task-agent`):** Apply controls.
- **Review mode (`review-agent`):** Judge proof.

## When To Use

- proved trust, privilege, permission, privacy, credential, or secret boundary change with a reachable abuse or disclosure path
- credential or session lifecycle behavior change

## Do Not Use

- no trust boundary impact
- self review request
- internal refactor with evidence that credential and session lifecycle behavior is unchanged
- reliability-only failure with no abuse or privacy risk
- input shape change with no security sink
- scanner report organization without a security verdict
- security terminology, a permission API, path mutability, or future replacement possibility without a proved trust, privilege, secret, or privacy boundary change
- bounded same-principal non-sensitive local access with no privilege elevation or less-trusted writer

## Required Inputs

- acceptance and trust boundary summary
- **Analysis mode (`analysis-agent`):** affected assets, actors, entry points, sinks, and current control evidence.
- **Task mode (`task-agent`):** accepted control decision and denied-path and abuse-case checks.
- **Review mode (`review-agent`):** changed trust boundary and exploit-relevant evidence.

## Professional Decision Rules

- Trace authority to asset and sink.
- Gate controls on current denial/containment evidence.
- Reject abuse without a privilege path or less-trusted writer.

## High-Value Gotchas

- Authentication is not object-level authorization; redaction after serialization is late.
- A security claim without negative-path evidence remains unverified.

## Execution Checklist

1. Confirm the active asset, actor, controlled source, reachable sink, and accountable owner.
2. Select the named Reference owning the reachable-path control decision.
3. Verify denied behavior, containment, proof limits, and residual exposure.
4. Stop when exploit-relevant evidence does not establish policy, reachability, and control applicability.
5. **Analysis mode:** Select controls from the reachable path.
6. **Task mode:** Apply controls at the effective boundary.
7. **Review mode:** Judge denied paths, containment, and residual exposure.

## Stop / Escalation Conditions

- Stop on incomplete security closure evidence.

## Output Contract

- abuse-path model; trust-boundary changes; security verdict.
- **Analysis mode (`analysis-agent`):** abuse-path model; control strategy; unknown exposure.
- **Task mode (`task-agent`):** trust-boundary changes; denied-case evidence; unverified exposure.
- **Review mode (`review-agent`):** security verdict; reachable findings; residual exposure.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 mode needs compact checks for its triggered authorization, input/output, secret, dependency, privacy, cloud, AI, or tool risk | The root gate is enough or mode-specific closure and targeted proof are required | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on command/report artifacts, exit code, denied-case proof, scanner evidence, sandbox classification, freshness, or proof limits | No selected security claim depends on runtime evidence or the root contract is sufficient | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing security privacy gate references require dependency, conflict, or output-fragment selection | the security privacy gate root or a task-named reference already resolves selection | analysis-agent, task-agent, review-agent | reference-selection |
| [security output and gates](references/security-output-and-gates.md) | targeted | L3-L5 work needs mode-specific closure and targeted gates for a selected authorization, abuse, secret, dependency, privacy, cloud, AI, or tool-authority risk | A compact L1/L2 result is sufficient and no selected risk needs the extended proof contract | analysis-agent, task-agent, review-agent | gate-decision, residual-risk |
