---
name: security-privacy-gate
description: "`analysis-agent`: analyze permissions, secrets, sensitive data, trust boundaries and injection; `task-agent`: implement controls; `review-agent`: assess evidence. Skip self-review or no security/privacy lifecycle impact."
---

# security-privacy-gate

## Role

- **Analysis mode (`analysis-agent`):** Trace paths.
- **Task mode (`task-agent`):** Apply controls.
- **Review mode (`review-agent`):** Judge proof.

## When To Use

- proved trust, privilege, permission, credential, or secret boundary change with a reachable abuse or disclosure path
- evidenced personal-data purpose, processing, retention, deletion, or other lifecycle change with a concrete privacy consequence
- credential or session lifecycle behavior change

## Do Not Use

- no security boundary or privacy lifecycle impact
- self review request
- internal refactor with evidence that security controls and credential, session, and privacy lifecycle behavior are unchanged
- reliability-only failure with no abuse or privacy risk
- input shape change with no security sink or privacy lifecycle consequence
- scanner report organization without a security verdict
- security terminology, a permission API, path mutability, or future replacement possibility without a proved trust, privilege, secret, or privacy boundary change
- bounded same-principal non-sensitive local access with no privilege elevation or less-trusted writer

## Required Inputs

- acceptance and security boundary or privacy lifecycle summary
- **Analysis mode (`analysis-agent`):** affected assets or personal-data flows, actors, security paths or lifecycle consequences, and current control evidence.
- **Task mode (`task-agent`):** accepted control decision and applicable denied-path, abuse-case, or privacy lifecycle checks.
- **Review mode (`review-agent`):** changed security or privacy behavior and exploit-relevant or purpose/lifecycle evidence for the selected claim.

## Professional Decision Rules

- Trace security authority to asset and sink.
- Trace personal-data use to accepted purpose, lifecycle obligations, and actual individual consequences, even without an attacker.
- Gate controls on current denial, containment, or privacy lifecycle evidence appropriate to the selected risk.
- Reject abuse without a privilege path or less-trusted writer.

## High-Value Gotchas

- Authentication is not object-level authorization; redaction after serialization is late.
- A security claim without negative-path evidence remains unverified.

## Execution Checklist

1. Confirm the asset or personal-data flow, actor, source, accountable owner, and security path or privacy lifecycle consequence.
2. Select the named Reference owning the active control decision.
3. Verify applicable denied behavior, containment, purpose, retention, or deletion outcomes and their proof limits.
4. Stop when evidence cannot establish the selected policy, reachable security path or actual privacy consequence, and control applicability.
5. **Analysis mode:** Select controls from the security path or accepted privacy lifecycle obligation.
6. **Task mode:** Apply controls at the effective boundary.
7. **Review mode:** Judge the applicable denial, containment, or lifecycle results and residual risk.

## Stop / Escalation Conditions

- Stop on incomplete evidence for the selected security or privacy claim.

## Output Contract

- security-path or privacy-lifecycle model; control changes; security/privacy verdict.
- **Analysis mode (`analysis-agent`):** security-path or privacy-lifecycle model; control strategy; unknown risk.
- **Task mode (`task-agent`):** control changes; applicable denial or lifecycle evidence; unverified risk.
- **Review mode (`review-agent`):** security/privacy verdict; evidenced findings; residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded mode needs compact checks for its triggered authorization, input/output, secret, dependency, privacy, cloud, AI, or tool risk | The root gate is enough or mode-specific closure and targeted proof are required | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on command/report artifacts, exit code, denied-case proof, scanner evidence, sandbox classification, freshness, or proof limits | No selected security or privacy claim depends on runtime evidence or the root contract is sufficient | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing security privacy gate references require dependency, conflict, or output-fragment selection | the security privacy gate root or a task-named reference already resolves selection | analysis-agent, task-agent, review-agent | reference-selection |
| [security output and gates](references/security-output-and-gates.md) | targeted | work needs mode-specific closure and targeted gates for a selected authorization, abuse, secret, dependency, privacy, cloud, AI, or tool-authority risk | A compact result is sufficient and no selected risk needs the extended proof contract | analysis-agent, task-agent, review-agent | gate-decision, residual-risk |
