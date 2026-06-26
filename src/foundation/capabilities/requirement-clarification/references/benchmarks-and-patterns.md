# Requirement Clarification Benchmarks and Patterns

Use this reference when a clarification decision needs deeper classification support. Keep `SKILL.md` focused on routing and output; this file carries decision trees, templates, and examples.

## Benchmark Anchors

- ISO/IEC/IEEE 29148 and IEEE 830: requirements should be complete, consistent, unambiguous, feasible, verifiable, and traceable.
- Agile Definition of Ready: stories should not enter implementation while blocking questions, dependencies, or acceptance gaps remain.
- RFC 2119: use MUST, SHOULD, MAY, MUST NOT, and SHOULD NOT to separate binding requirements from informative notes.
- OWASP ASVS: security and authorization requirements are implementation blockers, not optional details.
- Product discovery known-knowns/known-unknowns practice: clarification turns hidden assumptions into explicit facts, questions, or rejected guesses.
- Evidence-based engineering execution: current source, current tests, generated contracts, telemetry, and owner decisions outrank stale memory or informal chat.

## Classification Matrix

| Gap type | Blocking by default? | Non-blocking only when | Evidence needed |
| --- | --- | --- | --- |
| Authorization or tenant scope | Yes | Authority approves a bounded, reversible default that does not broaden access. | Owner decision, denied-case acceptance, security gate. |
| Payment, billing, refund, ledger, entitlement | Yes | Read-only investigation or UI copy can proceed without financial behavior. | Product/finance owner, reconciliation impact, rollback path. |
| Data migration, retention, deletion, data loss | Yes | Work is limited to discovery or reversible scaffolding that does not alter data. | Data owner, migration/rollback decision, current data evidence. |
| Public API, SDK, event, generated contract | Yes | Additive internal prep does not change public contract or generated artifacts. | Consumer impact owner, old/new behavior statement. |
| Compliance, privacy, legal, audit | Yes | Legal/compliance owner names a safe constraint and evidence requirement. | Control owner, evidence owner, retention/freshness. |
| UX copy, labels, visual polish | Usually no | Copy/design can be isolated from API/schema/permission behavior. | Safe default, design/product owner, follow-up. |
| Telemetry naming or dashboard polish | Usually no | Metric contract, labels, and cardinality are not affected. | Observability owner, not-present or rename path. |
| Unknown exact rollout date | Usually no | Implementation can stay disabled or unreleased safely. | Release owner, feature flag/rollback constraint. |
| Stakeholder claim about existing data | Yes until verified | Current data/source proves the claim or code avoids relying on it. | Query/report/source evidence and freshness. |
| Project memory claim | No as a lead; yes if used as authority | Current source confirms it or it is marked advisory only. | Inspected paths, accepted/rejected memory. |

## Blocking Decision Tree

```
Could the answer change a public contract, data model, permission, lifecycle,
migration, rollback, compliance obligation, financial record, or irreversible action?
  YES -> Blocking unknown.
  NO  -> Continue.

Can work be fully isolated behind copy, config, docs, discovery, or a bounded
follow-up without changing public behavior or data?
  NO  -> Blocking unknown.
  YES -> Continue.

Is the safe default reversible, conventional for this repository, testable, and
outside product/security/legal authority?
  NO  -> Blocking unknown or explicit stakeholder assumption.
  YES -> Non-blocking unknown or safe engineering assumption.

Is there a named owner, validation check, and expiry/trigger?
  NO  -> Incomplete classification.
  YES -> Proceed only within the minimum safe scope.
```

## Clarification Record Template

```markdown
## Clarification Record

mode_selected: ambiguity triage
request_summary: [Neutral 1-2 sentence statement.]

boundaries_inspected:
- Request source:
- Current source/docs/tests:
- Registry/generated artifacts:
- Reports/telemetry:
- Project memory / repository graph:
- Skipped with reason:

source_evidence:
- Verified fact:
- Stakeholder claim:
- Current-source conflict:

graph_memory_trajectory_judgment:
- Accepted:
- Rejected:
- Not verified:

blocking_unknowns:
| id | question | category | owner | decision needed | why blocking | downstream gate |

non_blocking_unknowns:
| id | question | safe default | isolation | follow-up owner | validation/check |

safe_engineering_assumptions:
- [Assumption, why reversible/conventional/testable.]

explicit_stakeholder_assumptions:
- [Claim, source, verification needed.]

unsafe_assumptions_rejected:
- [Shortcut, risk, required evidence.]

proceed_block_decision:
- Status: BLOCK / PROCEED / PARTIAL PROCEED
- Justification:

minimum_safe_scope:
- Can implement now:
- Must wait:
- Forbidden assumptions/artifacts:

changed_clarification_to_validation_map:
- [Question/assumption/evidence/default] -> [owner response/test/review/residual risk]

handoff_boundaries:
- Next capability:
- Specialist gates:

evidence_limits:
- [Uninspected or unverified evidence and owner.]
```

## Graph, Memory, and Trajectory Coupling

- Repository graph answers "where might this requirement touch?" It does not answer product intent. Use it to find routes, schemas, tests, generated files, docs, consumers, and ownership boundaries.
- Project memory answers "what has mattered before?" It does not prove current behavior. Accept memory only when current source, fresh reports, or owner decisions confirm it.
- Execution trajectory answers "what did the agent already try or skip?" It does not prove correctness. Use it to avoid repeated same-path attempts, stale validation, and unreviewed repairs.
- Clarification output should state whether each graph/memory/trajectory claim was accepted, rejected, or not verified.

## Partial Proceed Pattern

Partial proceed is valid only when:

- Blocking unknowns are outside the proposed safe slice.
- Safe slice has no public contract, data mutation, authority, migration, or irreversible behavior dependency on the unresolved answer.
- Must-wait work is named as forbidden until the owner response arrives.
- Tests or review checks can prove forbidden artifacts did not appear.
- Follow-up owner and trigger are explicit.

Examples:

- Safe: Read-only repository discovery can proceed while product decides authorization behavior.
- Safe: UI copy key can be created while final wording is pending, if API field names and behavior are fixed.
- Unsafe: Creating a nullable `future_policy_id` column while policy ownership is undecided.
- Unsafe: Adding a disabled endpoint for a future workflow that has no approved contract.

## Owner Response Shape

Every owner response should include:

- Decision: exact answer or approved safe default.
- Scope: which actors, surfaces, data, versions, tenants, or environments the answer covers.
- Evidence: source, meeting record, ticket comment, policy, data query, or contract reference.
- Expiry or revisit trigger: when the decision must be revisited.
- Downstream gate: structuring, non-goal boundary, acceptance, data/API, security, release, reliability, or quality.

## Anti-Pattern Review

| Anti-pattern | Why it fails | Corrective action |
| --- | --- | --- |
| "Assume admin-only." | Hidden authorization policy. | Blocking owner decision. |
| "Product said no existing data violates this." | Unverified data claim. | Query/report or mark stakeholder assumption. |
| "Copy later." but field names follow copy. | Copy leaks into API contract. | Isolate copy from schema/API. |
| "Memory says this path exists." | Stale context can route work wrong. | Inspect current source and callers. |
| "Proceed except risky part" without forbidden artifacts. | Scope creep remains invisible. | Add not-present checks. |
| "We can ask later" without owner. | Deferred question becomes permanent. | Add owner, trigger, and residual risk. |

## Validation Mapping Examples

- Blocking auth question -> owner answer plus security gate or denied-path acceptance.
- Stakeholder data claim -> source query/report or residual risk.
- Safe default for sort order -> test/config check proving it is isolated.
- Deferred copy -> i18n key review proving no API field naming dependency.
- Partial proceed -> diff/API/schema/UI/job/flag search proving forbidden artifacts absent.
- Memory claim -> current source/caller search accepting or rejecting it.
