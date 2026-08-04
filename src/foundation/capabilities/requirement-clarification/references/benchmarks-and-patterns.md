# Requirement Clarification Benchmarks And Patterns

Load this reference when an unknown can change observable behavior, authority, data, contract, migration, release, compliance, or an irreversible outcome. Do not load it to delay a reversible engineering choice already governed by current repository convention.

## Blocking Classification

| Unknown affects | Blocking unless | Required evidence and owner |
| --- | --- | --- |
| Authorization, tenant/object scope, support/admin authority | A bounded default cannot broaden access and the policy owner accepts it. | Actor/action/resource/scope decision, denied behavior, and security/permission owner. |
| Payment, ledger, billing, entitlement, refund, or irreversible mutation | The slice is read-only/discovery and cannot alter financial or durable outcome. | Product/finance/domain owner, reconciliation and rollback/irreversibility decision. |
| Migration, retention, deletion, historical data, or data loss | The slice neither mutates nor precommits a future schema/contract. | Data owner, current-data evidence, mixed-version/rollback decision. |
| Public API/SDK/event/generated contract or compatibility | The slice is internal, additive preparation with no emitted/registered public artifact. | Consumer/contract owner, old/new behavior, version and rollout boundary. |
| Privacy, legal, compliance, audit, or security control | The accountable control owner supplies the constraint and evidence bar. | Scoped owner decision, policy/control source, retention and verification. |
| Copy, visual detail, telemetry presentation, or rollout date | It is isolated from names/contracts/policy and a reversible default is accepted. | Forbidden dependency/artifact check, follow-up owner, expiry/revisit trigger. |

The consequence determines blocking status; the category alone does not. Repository code, historical notes, analytics, or a stakeholder assertion may reveal a question but do not decide product intent or policy.

## Partial Proceed Boundary

Use a partial-proceed slice when it is reversible, independently testable, and independent of the blocking answer; keep it outside public contracts, schema/data mutation, authority expansion, release activation, and speculative future artifacts. Record the executable scope, deferred boundary, a not-present check, follow-up owner, and trigger. If isolation is unproven, block and return the missing decision instead of manufacturing a “safe default.”

Treat an unknown as an engineering assumption only when repository convention supports a reversible, testable choice outside product, security, or legal authority. Otherwise, classify it as blocking or non-blocking with an accountable owner. A stakeholder assumption records source, scope, date, and required verification. It is not a fact.

## Evidence, Response, And Routes

For each unknown record exact question, consequence, decision owner, accepted/rejected/stale evidence, minimum safe scope, and validation or residual-risk owner. An owner response states decision, actor/surface/data/version/environment scope, authoritative source, expiry/revisit trigger, and downstream handoff.

Repository inspection proves only paths searched; prior evidence is a lead; command history proves only actions taken. None proves product intent, production data, external contracts, or stakeholder authority. State those limits.

Reject “assume admin-only,” unsupported data claims, “risky part later” without forbidden artifacts, nullable/future placeholders, remembered behavior as authority, and deferral without owner/expiry. Route stable facts to `requirement-structuring`, exclusions to `non-goal-boundary-definition`, scenarios/criteria to `scenario-decomposition` and `acceptance-standard-definition`, and material contract/data/security/release gaps to their named Professional owner.
