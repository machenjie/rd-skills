---
name: security-privacy-gate
description: "Use `analysis-agent` to analyze permissions, secrets, sensitive data, trust boundaries, and injection; `task-agent` to implement controls; and `review-agent` to assess evidence. Skip self-review and no-trust-impact work."
---

# security-privacy-gate

## Role

- **Analysis mode (`analysis-agent`):** Model reachable abuse paths and select controls.
- **Task mode (`task-agent`):** Apply accepted trust-boundary controls.
- **Review mode (`review-agent`):** Judge controls against reachable abuse paths.

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

- acceptance
- trust boundary summary
- **Analysis mode (`analysis-agent`):** affected assets, actors, entry points, sinks, and current control evidence.
- **Task mode (`task-agent`):** accepted control decision with denied-path and abuse-case checks.
- **Review mode (`review-agent`):** changed trust boundary with exploit-relevant evidence.

## Professional Decision Rules

- Model affected assets, actors, trust boundaries, abuse paths, and data lifecycle before selecting controls.
- Mutability or future replacement alone does not prove a reachable abuse path.
- Bounded same-principal non-sensitive local access without privilege elevation or a less-trusted writer is not a material trust-boundary change by itself.
- Enforce changed actor, object, or tenant authorization from authenticated server context; UI hiding is not authorization.
- Select controls from the actual sink, deployment, data classification, effective policy, and reachable abuse path.
- Validate triggered negative paths with explicit residual exposure when dynamic proof is unavailable.

## High-Value Gotchas

- Authentication is not object-level authorization; redaction after serialization is late.
- A security claim without negative-path evidence remains unverified.

## Execution Checklist

1. Trace attacker-controlled data and authority from entry point to asset, sink, and disclosure path.
2. Choose authorization, validation, containment, and lifecycle controls from the reachable abuse path.
3. Verify denied cases, tenant isolation, secret handling, and residual exposure where triggered.
4. **Analysis mode:** select controls from the reachable abuse path.
5. **Task mode:** apply controls at the effective trust boundary.
6. **Review mode:** judge denied paths, containment, and residual exposure.
7. Stop when trust boundaries, policy, or exploit-relevant evidence remain unknown.

## Stop / Escalation Conditions

- Block authorization, tenant, or session changes without server-side denied-path proof; require CSRF proof only for unproven ambient browser authority.
- Block attacker-controlled data reaching a sensitive sink without abuse-path proof and a sink-specific control.
- Block secret, dependency, cloud, or key work without an owner, policy, containment, and rotation path.
- Block privacy or compliance closure when a triggered obligation lacks control, evidence, owner, or exception.
- Set severity from exploitability and current release policy, not scanner labels.
- Refuse risky tool execution without authority, isolation, recovery, and redaction evidence.

## Output Contract

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
