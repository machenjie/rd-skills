# Skill Professionalism Dimension Rubric

Status: normative scoring rubric  
Applies to: rd-skills professional skills, foundation capabilities, and domain extensions
Score model: 100-point professionalism score, independent from activation quality and context efficiency

---

## Reader Path

- Start with [Score Summary](#2-score-summary) to understand the total weighting.
- Use the dimension sections when reviewing one skill; each dimension now has a unique full-credit and scoring anchor.
- Use [Type-Specific Minimums](#14-type-specific-minimums) and [Manual Review Checklist](#15-manual-review-checklist) before recording a final score.

## 1. Purpose

This rubric defines the dimensions used to evaluate whether a skill's content is professionally deep enough for its declared responsibility.

The rubric must be used for:

- manual skill review;
- static professionalism evaluation;
- professional benchmark fixture design;
- regression baseline comparison;
- release readiness review;
- authoring guidance for new skills and capabilities.

This rubric evaluates professional content only. It must not award professionalism points for trigger accuracy, reference precision, small body size, or low token cost.

---

## 2. Score Summary

| Dimension | Points |
|---|---:|
| Professional Responsibility Clarity | 8 |
| Domain Judgment Depth | 15 |
| Decision Criteria Completeness | 12 |
| Failure Mode Specificity | 12 |
| Evidence Contract Completeness | 12 |
| Output Contract Actionability | 10 |
| Boundary and Ownership Precision | 9 |
| Trade-Off Priority Quality | 7 |
| Anti-Pattern Quality | 7 |
| Validation Semantics | 5 |
| Residual Risk Handling | 3 |
| **Total** | **100** |

Recommended status bands:

| Score | Status | Meaning |
|---:|---|---|
| 95-100 | sample-grade | can serve as a reference example |
| 85-94 | release-grade | professionally strong enough for release |
| 75-84 | needs-review | usable but has professional-depth gaps |
| 60-74 | weak | lacks important professional judgment |
| < 60 | failing | structurally present but professionally insufficient |

Release policy:

```text
professionalism_score >= 85
no core dimension below 70%
no release-blocking professional gap
```

Core dimensions:

```text
domain_judgment_depth
decision_criteria_completeness
failure_mode_specificity
evidence_contract_completeness
output_contract_actionability
boundary_and_ownership_precision
```

---

## 3. Dimension 1: Professional Responsibility Clarity — 8 points

Measures whether the skill clearly declares the professional work it owns.

### Dimension 1 Full Credit

```text
owned decisions are explicit
non-owned decisions are explicit
primary user/work surface is explicit
expected professional output is explicit
professional failure risk is explicit
```

### Dimension 1 Scoring

| Score | Criteria |
|---:|---|
| 8 | Scope, ownership, output, and primary risk are all explicit and skill-specific |
| 6 | Scope and output are clear, but non-owned work or primary risk is incomplete |
| 4 | General responsibility is understandable, but boundaries are weak |
| 2 | Reads like a broad workflow or topic area |
| 0 | No clear professional responsibility |

### Common failures

- The skill says what topic it covers but not what decision it owns.
- The skill owns "everything" in a broad engineering area.
- The skill does not name what it must hand off.

---

## 4. Dimension 2: Domain Judgment Depth — 15 points

Measures whether the skill contains expert judgment axes specific to its declared scope.

### Dimension 2 Full Credit

At least 6 strong judgment axes for professional skills, 4 for foundation capabilities, and 5 for domain extensions.

Each axis must answer:

```text
what decision it changes
what evidence it needs
what failure it prevents
when it escalates or hands off
```

### Dimension 2 Scoring

| Score | Criteria |
|---:|---|
| 15 | Skill-specific judgment axes are complete, decision-changing, and evidence-bound |
| 12 | Strong axes exist but one or two are shallow or lack evidence |
| 9 | Several axes exist but some are generic or not decision-changing |
| 6 | Mostly checklist-like content with limited expert judgment |
| 3 | Generic best-practice language dominates |
| 0 | No meaningful professional judgment axes |

### Examples of good axes

Backend skill:

```text
authorization boundary
transaction consistency
idempotency/retry behavior
side-effect ordering
service placement
error contract
observability for failure diagnosis
release/rollback exposure
```

Frontend skill:

```text
state ownership
API error behavior
accessibility
loading/empty/error states
user-visible compatibility
client/server contract drift
performance budget
interaction regression
```

Domain extension:

```text
irreversible domain mutation
domain data authority
settlement/reconciliation
custody/security
domain validation/golden cases
domain release evidence
```

---

## 5. Dimension 3: Decision Criteria Completeness — 12 points

Measures whether the skill gives enough criteria to make correct professional decisions.

### Dimension 3 Full Credit

```text
ordered decision rules
mode-specific criteria
blocking vs non-blocking unknown classification
escalation criteria
skip criteria
default decisions with escape conditions
```

### Dimension 3 Scoring

| Score | Criteria |
|---:|---|
| 12 | Ordered, mode-aware, evidence-based decision rules cover the skill's professional surface |
| 10 | Strong decision rules exist with minor mode or skip gaps |
| 8 | Useful rules exist but ordering or escalation is incomplete |
| 5 | Rules are mostly checklist statements |
| 2 | Rules are generic advice |
| 0 | No decision criteria |

### Good rule pattern

```text
If <evidence condition>, then <professional decision>, because <risk>, and require <proof>.
```

### Bad rule pattern

```text
Consider <topic>.
Handle <risk>.
Make sure <quality>.
```

---

## 6. Dimension 4: Failure Mode Specificity — 12 points

Measures whether the skill names concrete, skill-specific ways work fails.

### Dimension 4 Full Credit

Each important failure mode includes:

```text
failure condition
consequence
detection signal
prevention or repair action
evidence required
```

### Dimension 4 Scoring

| Score | Criteria |
|---:|---|
| 12 | Failure modes are concrete, consequence-bearing, and tied to detection/prevention |
| 10 | Strong failure modes exist but some lack detection or repair |
| 8 | Failure list is relevant but consequence depth is inconsistent |
| 5 | Failure modes are partly generic |
| 2 | Failure modes are labels without consequences |
| 0 | No meaningful failure modes |

### Strong example

```text
Failure: retry path duplicates a side-effecting operation.
Consequence: duplicate payment/refund/job mutation.
Detection: retry source exists and idempotency key scope is undefined.
Prevention: define durable dedupe key and duplicate-delivery validation.
Evidence: replay test or explicit not-verified residual risk.
```

### Weak example

```text
Failure: poor retry handling.
```

---

## 7. Dimension 5: Evidence Contract Completeness — 12 points

Measures whether the skill requires proof that matches the professional risks it closes.

### Dimension 5 Full Credit

```text
inspected boundaries
evidence source
what evidence proves
what evidence does not prove
missing evidence handling
residual risk
next gate
```

### Dimension 5 Scoring

| Score | Criteria |
|---:|---|
| 12 | Evidence contract covers proof, limits, residual risk, and next gate |
| 10 | Strong evidence contract with minor missing edge cases |
| 8 | Evidence is required but proof/limits are incomplete |
| 5 | Evidence is mostly command/test listing without semantic mapping |
| 2 | Evidence is implied by prose |
| 0 | No evidence contract |

### Strong evidence categories

```text
source inspected
test inspected
test run
behavior reproduced
contract compared
diff reviewed
same-pattern scan completed
runtime output captured
manual verification explicitly scoped
```

### Invalid evidence categories

```text
agent claims it considered the issue
unchecked checklist
generated prose
unrun test plan described as proof
self-review by owner with no independent gate
```

---

## 8. Dimension 6: Output Contract Actionability — 10 points

Measures whether the skill's required output lets the next actor continue without guessing.

### Dimension 6 Full Credit

Output must include:

```text
selected mode
professional decision
inspected boundaries
evidence collected
evidence limits
required action or review finding
validation status
residual risk
next owner/gate
```

### Dimension 6 Scoring

| Score | Criteria |
|---:|---|
| 10 | Output is directly usable by implementer/reviewer/tester/release owner |
| 8 | Output is actionable but misses one closure field |
| 6 | Output is understandable but needs interpretation |
| 4 | Output is mostly explanatory |
| 2 | Output is a prose summary |
| 0 | No output contract |

### Output must not

- force full ceremonial output for trivial tasks;
- hide missing evidence;
- report "done" without validation or residual risk;
- omit handoff when another skill owns the remaining risk.

---

## 9. Dimension 7: Boundary and Ownership Precision — 9 points

Measures whether the skill prevents ownership confusion.

### Dimension 7 Full Credit

```text
owned scope
non-owned scope
adjacent skill boundary
owner/reviewer/gate role
handoff rule
composition rule for capabilities or domain extensions
```

### Dimension 7 Scoring

| Score | Criteria |
|---:|---|
| 9 | Ownership, non-ownership, adjacent boundaries, and handoff are precise |
| 7 | Boundaries are clear with minor adjacent-skill gaps |
| 5 | Scope exists but adjacent ownership is weak |
| 3 | Boundary mostly inferred |
| 0 | No meaningful boundary |

### Professional ownership rule

A skill must not own work only because it can discuss the topic. It owns work only when its output owns the next professional action.

---

## 10. Dimension 8: Trade-Off Priority Quality — 7 points

Measures whether the skill defines expert priority when goals conflict.

### Dimension 8 Full Credit

At least 4 skill-specific priority rules.

Examples:

```text
authorization safety before reuse
public compatibility before internal cleanup
behavior preservation before refactor elegance
rollback evidence before release speed
diagnosability before silent fallback
domain correctness before UI convenience
```

### Dimension 8 Scoring

| Score | Criteria |
|---:|---|
| 7 | Skill-specific trade-off priorities are explicit and action-changing |
| 5 | Good priorities exist but are incomplete |
| 3 | Priorities are generic |
| 0 | No trade-off guidance |

### Bad examples

```text
Balance quality and speed.
Be pragmatic.
Use good judgment.
```

---

## 11. Dimension 9: Anti-Pattern Quality — 7 points

Measures whether the skill teaches the agent to avoid common professional mistakes.

### Dimension 9 Full Credit

Each anti-pattern includes:

```text
wrong behavior
why wrong
detection signal
replacement action
```

### Dimension 9 Scoring

| Score | Criteria |
|---:|---|
| 7 | Anti-patterns are specific, detectable, and include replacements |
| 5 | Anti-patterns are useful but not all have replacements |
| 3 | Anti-patterns are mostly warning labels |
| 0 | No anti-pattern content |

### Good anti-pattern

```text
Wrong: add a new abstraction because two functions look similar.
Why wrong: similarity may be accidental; abstraction can hide ownership and lifecycle differences.
Detect: callers differ in state ownership, error contract, or release cadence.
Replacement: keep local duplication until stable shared invariants emerge.
```

---

## 12. Dimension 10: Validation Semantics — 5 points

Measures whether validation is tied to what it proves.

### Dimension 10 Full Credit

```text
validation method
risk covered
expected outcome
what remains unproven
fallback when validation cannot run
```

### Dimension 10 Scoring

| Score | Criteria |
|---:|---|
| 5 | Validation maps clearly to risk and evidence limits |
| 4 | Validation is concrete but limits are incomplete |
| 3 | Commands/checks are named but semantic proof is weak |
| 1 | Generic "run tests" language |
| 0 | No validation semantics |

---

## 13. Dimension 11: Residual Risk Handling — 3 points

Measures whether unverified professional risk is made explicit.

### Dimension 11 Full Credit

```text
residual risk
reason not verified
owner
next gate or follow-up
compensating evidence
```

### Dimension 11 Scoring

| Score | Criteria |
|---:|---|
| 3 | Residual risk ownership and next gate are explicit |
| 2 | Residual risk named but ownership or next gate incomplete |
| 1 | Generic "some risk remains" |
| 0 | No residual-risk handling |

---

## 14. Type-Specific Minimums

### 14.1 Professional Skills

Required minimums:

```text
professionalism_score >= 85
domain_judgment_depth >= 12/15
decision_criteria_completeness >= 10/12
failure_mode_specificity >= 10/12
evidence_contract_completeness >= 10/12
output_contract_actionability >= 8/10
```

Release-blocking gaps:

```text
missing owned decisions
missing failure modes
missing evidence contract
missing output contract
missing boundary/handoff
professionalism_score < 85
```

### 14.2 Foundation Capabilities

Required minimums:

```text
professionalism_score >= 82
domain_judgment_depth >= 10/15
decision_criteria_completeness >= 9/12
failure_mode_specificity >= 8/12
evidence_contract_completeness >= 9/12
output_contract_actionability >= 8/10
```

Release-blocking gaps for key capabilities:

```text
acts as top-level owner
no narrow decision responsibility
no required input fragment
no output fragment
no return-to-owner rule
```

### 14.3 Domain Extensions

Required minimums:

```text
professionalism_score >= 88
domain_judgment_depth >= 12/15
failure_mode_specificity >= 10/12
evidence_contract_completeness >= 10/12
boundary_and_ownership_precision >= 8/9
```

Release-blocking gaps:

```text
keyword-only domain activation
no weak-signal rejection
no owner composition rule
domain rules not domain-specific
claims domain safety/compliance without evidence
```

---

## 15. Manual Review Checklist

```text
[ ] The skill owns a real professional decision.
[ ] The skill's professional judgment axes are skill-specific.
[ ] Decision rules are ordered and evidence-based.
[ ] Failure modes include consequences and detection.
[ ] Evidence says what it proves and does not prove.
[ ] Validation maps to risks.
[ ] Output is usable by the next actor.
[ ] Boundaries and handoff are explicit.
[ ] Trade-off priority is explicit.
[ ] Anti-patterns include detection and replacement.
[ ] Residual risk ownership is required.
[ ] Professional score is not inflated by activation or context-efficiency traits.
```
