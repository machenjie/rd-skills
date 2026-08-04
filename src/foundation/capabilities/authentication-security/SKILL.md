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

Protect authentication issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, recovery, linking, and compromise response.

## High-Value Rules

- Start from the current threat model, identity provider, assurance requirement, organization policy, regulatory boundary, performance budget, and recovery UX; do not substitute fixed credential, token, cookie, magic-link, or MFA values.
- When local passwords are stored, use a platform-supported password hashing/KDF with policy-derived parameters and measured capacity instead of fast hashes or custom cryptography.
- Define credential lifecycle controls across issuance, transport, storage, renewal, privilege change, rotation, revocation, logout, and compromise response.
- Select session or token controls from the actual client, identity provider, deployment, and replay boundary.
- Treat recovery and account linking as authentication paths. Choose factor strength, rate controls, notifications, verification, session invalidation, and negative-flow proof from takeover impact and current policy.

## Anti-Patterns

- Clearing a client cookie is not revocation when a refresh token or server session remains valid.
- Recovery, email change, federation, or account linking can bypass stronger controls on the primary login path.

## Execution Checklist

1. Map actors, credentials, IdP trust, session/token families, privilege transitions, recovery paths, and compromise events.
2. Verify current provider capabilities, signing/key policy, browser cookie model, revocation store, performance/UX constraints, and applicable organizational policy before choosing controls.
3. Prove reachable attack paths and record untested paths, evidence limits, and residual takeover risk.

## Stop Conditions

- Escalate admin/payment actions, regulated data, account recovery/linking, federation trust, elevated service accounts, persistent device trust, or cross-domain cookies when the threat model, IdP evidence, exception owner, or residual takeover risk is unclear.

## Output Contract

- authentication security review with controls failure cases and audits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Credential, session, federation, or recovery controls require mechanism selection | No authentication lifecycle or assurance boundary changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Affected flows include compromise, revocation, linking, or step-up denial | The change cannot issue, renew, recover, or revoke identity | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Authentication claims need fresh replay, fixation, or redaction proof | No lifecycle control claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
