# Domain Extension Authoring Standard

Status: normative overlay  
Version: v2  
Extends: ChangeForge Skill Authoring Base Standard  
Applies to: `changeforge_kind: domain-extension`  
Role: optional domain risk and constraint addendum for full/dev profiles

---

## 1. Purpose

Domain extensions add domain-specific constraints, risk, terminology, evidence, and validation to a selected professional owner skill.

A domain extension must not:

- replace the primary professional owner;
- close ordinary engineering work alone;
- activate on keyword-only signals;
- load full domain depth by default;
- become a standalone domain mega-skill.

It must:

- require strong domain signals;
- reject weak signals;
- compose with a professional owner;
- return a domain output addendum;
- hand control back to owner/gate/reviewer.

---

## 2. Required Frontmatter

```yaml
---
name: payment-trading-extension
description: Use this domain extension when a selected professional skill handles payment, subscription, billing, refund, chargeback, trading, ledger, balance, settlement, entitlement, tax, or irreversible financial state behavior.
license: MIT
changeforge_kind: domain-extension
changeforge_version: 0.1.0
metadata:
  changeforge.profile: full
  changeforge.skill_type: domain-extension
  changeforge.domain: payment-trading
---
```

Description must start with `Use this domain extension when `.

Budget:

```text
target: 260-420 chars
warning: >420
fail unless exception: >500
```

---

## 3. Required Section Order

```text
1. Domain Scope
2. Strong Domain Signals
3. Weak Signals That Are Not Enough
4. Do Not Use When
5. Required Professional Owner Skill
6. Domain-Specific Non-Negotiable Rules
7. Domain Risk Escalation
8. Domain Reference Loading Policy
9. Domain Output Addendum
10. Domain Quality Gate
11. Return / Escalate
12. Completion Criteria
```

All sections are required.

---

## 4. Domain Scope

Must define:

```text
domain boundary
material behaviors
professional owner surfaces it can augment
non-domain cases it rejects
false activation risk
```

---

## 5. Strong Domain Signals

Strong signals must indicate material domain behavior, not mere words.

Examples:

```text
domain state mutation
domain API or schema change
domain security/custody/permission risk
domain compliance evidence
domain reconciliation/rollback risk
domain irreversible operation
domain golden-case validation
domain incident or production risk
```

Each domain extension must list its own strong signals.

---

## 6. Weak Signals That Are Not Enough

Must explicitly reject:

```text
path/label/button/fixture/variable/title keyword only
copywriting-only change
UI styling-only change
documentation-only mention
test rename without semantic change
generic refactor with no domain contract/data/risk change
ambiguous word such as token/order/model without domain behavior
```

---

## 7. Do Not Use When

Must include:

```text
pure UI styling
copywriting only
documentation-only without domain behavior
fixture/test name only
keyword-only mention
no professional owner selected
professional skill can handle without domain-specific risk
```

---

## 8. Required Professional Owner Skill

A domain extension must compose with one primary professional owner.

Required format:

```text
- backend-change-builder: domain behavior implementation
- data-api-contract-changer: domain API/DTO/event/schema/SDK compatibility
- security-privacy-gate: domain authorization/privacy/custody/secret risk
- data-middleware-change-builder: domain storage/queue/cache/migration behavior
- reliability-observability-gate: domain SLO/replay/reconciliation/fallback risk
- delivery-release-gate: rollout/migration/rollback/compliance evidence
- quality-test-gate: domain golden cases/regression proof
```

If no owner exists:

```text
blocked: missing primary professional owner skill
```

---

## 9. Domain-Specific Non-Negotiable Rules

Rules must be domain-specific and enforceable.

Good:

```text
Do not grant entitlement from a frontend payment success callback.
```

Bad:

```text
Be careful with payments.
```

Keep 5-12 rules inline. Move deep catalogs to references.

---

## 10. Domain Risk Escalation

Must define escalation to:

```text
security-privacy-gate
data-api-contract-changer
data-middleware-change-builder
reliability-observability-gate
delivery-release-gate
quality-test-gate
professional owner skill
foundation capabilities
```

Escalation must be based on strong signal evidence, not keyword presence.

---

## 11. Domain Reference Loading Policy

A domain extension with `references/` must have `references/index.md`.

Policy must include:

```text
load only after primary owner selection
load only after strong domain signal
never load for keyword-only mentions
L1-L5 reference budget
required/forbidden reference rules
depends_on/conflicts_with from index
```

Every selected domain reference requires:

```text
domain_signal
owner_skill
reference_path
decision_supported
why_not_keyword_only
expected_addendum
```

---

## 12. Domain Output Addendum

The domain extension output is an addendum, not a full task result.

Required fields:

```text
domain_extension
strong_domain_signal
owner_skill
domain_rule_or_risk
additional_controls
domain_validation
domain_residual_risk
return_to_owner_or_gate
```

---

## 13. Domain Quality Gate

Pass only when:

```text
strong domain signal exists
weak-signal-only activation rejected
primary owner selected
domain rule changes decision or validation
domain references minimal
domain output is addendum
domain validation/residual risk explicit
escalation selected or skipped with rationale
```

---

## 14. Return / Escalate

Must return to:

```text
primary owner skill
selected gate
reviewer
blocked state when no owner exists
```

Format:

```text
Return to: <owner skill>
Domain addendum affects: <implementation/review/validation/release>
Escalate to: <gate or none>
Residual domain risk: <risk>
```

---

## 15. Domain Addendum Strictness

A domain extension violates the standard if it:

- produces full task output;
- owns implementation alone;
- closes engineering work alone;
- names controls without owner skill;
- selects unrelated professional skills;
- lacks residual domain risk;
- does not return to owner/gate.

---

## 16. Domain Reference Depth

Move to references:

```text
industry benchmark catalogs
risk matrices
large operation tables
anti-example catalogs
failure-mode catalogs
provider-specific details
regulatory details
deep validation matrices
```

Keep in `SKILL.md`:

```text
strong signals
weak-signal rejection
owner composition
5-12 domain rules
escalation rules
output addendum
quality gate
```

---

## 17. Legacy Section Migration

When standardizing an existing domain extension:

```text
Industry Benchmarks -> references/benchmarks-and-patterns.md
Operation matrices -> references/<domain>-operation-matrix.md
Risk Model -> references/<domain>-risk-model.md unless short
Anti-Examples -> references/anti-examples.md
Failure Modes -> reference unless short and critical
Linked Foundation Capabilities -> owner/capability composition table or references/index.md
```

Old domain sections are not automatically allowed to remain in body.

---

## 18. Domain Size

```text
target body: 140-220 lines
review: >260
mandatory split/tighten: >300
```

A domain extension over target is acceptable only when false-positive rejection or always-needed domain rules require it.

---

## 19. Domain Evaluation

Required evals:

```text
strong signal recall
weak signal rejection
keyword false positive
owner composition
domain reference loading
addendum quality
trace review
```

Recommended thresholds:

```text
strong_signal_recall >= 0.90
critical_domain_recall >= 0.95
weak_signal_rejection_rate >= 0.90
keyword_false_positive_rate <= 0.10
owner_composition_rate >= 0.90
```

Trace review must verify:

```text
extension not loaded before owner selection
not loaded for weak signals
only selected references loaded
addendum not full task output
return to owner/gate happens
```

---

## 20. Domain Anti-Patterns

Reject if the extension:

- activates on keyword-only signals;
- replaces owner skill;
- has no weak-signal rejection;
- loads all domain references;
- lacks reference index;
- produces standalone output;
- claims compliance without evidence;
- lacks domain validation;
- cannot name owner skill;
- keeps full benchmark/risk/anti-example catalogs in body without exception.

---

## 21. Domain Completion Gate

The domain extension is standardized complete only when:

```text
description within budget or exception
strong and weak signals explicit
owner composition concrete
domain rules enforceable
reference index exists if references exist
legacy deep content migrated or justified
output is addendum
weak-signal eval passes
owner composition eval passes
trace eval confirms no early/keyword-only activation
```
