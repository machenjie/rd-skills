# rd-skills Skill Professionalism Base Standard

Status: normative  
Applies to: all authored and built rd-skills Skill content
Skill types covered: professional skills, foundation capabilities, domain extensions  
Primary goal: evaluate whether the skill content itself expresses professional-grade judgment for its declared responsibility

---

## Reader Path

- Start with [Purpose](#1-purpose), [Definition of Skill Professionalism](#2-definition-of-skill-professionalism), and [Professionalism vs Efficiency](#3-professionalism-vs-efficiency) to understand the score boundary.
- Use [Required Professional Content Layers](#5-required-professional-content-layers) when reviewing a skill body or reference.
- Use the dimension rubric and evaluation/governance standard when scoring or releasing professionalism changes.

## 1. Purpose

This standard defines how rd-skills evaluates the **professional depth** of skill content.

It is intentionally separate from skill efficiency. A skill can be efficient, compact, correctly routed, and reference-light while still be professionally shallow. Conversely, a skill can contain professional knowledge but be inefficiently authored. rd-skills must evaluate both, but it must not collapse them into one score.

This standard answers:

```text
Does this skill teach the agent the right professional judgment for the work it claims to own?
```

It does not primarily answer:

```text
Will this skill activate efficiently?
Will this skill load few tokens?
Are references precisely loaded?
Is the body short enough?
```

Those are activation, routing, and context-efficiency concerns. They remain governed by the skill authoring and content-governance standards.

---

## 2. Definition of Skill Professionalism

A rd-skills skill is professionally strong when its `SKILL.md` and selected references enable the agent to make decisions that a competent senior engineer, reviewer, architect, tester, release owner, or domain specialist would make for that skill's declared scope.

Professionalism is not the presence of polished wording. It is the presence of domain-appropriate decision force.

A professional skill or capability must provide:

1. **Professional judgment axes** — the actual dimensions an expert checks.
2. **Decision criteria** — how to decide, not just what to remember.
3. **Risk prioritization** — what matters first when trade-offs conflict.
4. **Failure modes** — concrete ways work goes wrong in this skill's scope.
5. **Evidence requirements** — what proof is strong, weak, missing, or insufficient.
6. **Boundary ownership** — what this skill owns, what it must hand off, and what it must not claim.
7. **Anti-patterns** — common wrong paths, why they are wrong, and how to detect them.
8. **Validation semantics** — what validation proves and does not prove.
9. **Residual-risk handling** — what remains unverified and who owns the next gate.
10. **Output actionability** — an implementer, reviewer, or next skill can continue without guessing.

---

## 3. Professionalism vs Efficiency

Professionalism and efficiency must be reported separately.

| Concern | Question | Example dimension | Primary report |
|---|---|---|---|
| Professionalism | Is the skill's content professionally deep and correct for its declared scope? | decision criteria, failure modes, evidence, validation semantics | skill professionalism report |
| Activation quality | Does the skill trigger at the right time and avoid near misses? | trigger precision, mode selection, route quality | activation/routing report |
| Context efficiency | Does the skill avoid unnecessary body/reference loading? | body budget, reference precision, anti-bloat | skill content audit |
| Runtime behavior | Does the skill improve actual agent output? | with-skill vs without-skill delta | professional benchmark report |

A professionalism score must not increase because a skill is short, easy to route, or reference-efficient. Those may be required release gates, but they are not professional depth.

---

## 4. Scope

This standard applies to:

- `src/professional-skills/*/SKILL.md`
- `src/foundation/capabilities/*/SKILL.md`
- `src/domain-extensions/*/SKILL.md`
- skill-owned `references/`
- compiled capability references
- professional benchmark fixtures
- professionalism evaluation scripts
- professionalism regression baselines

It should not rewrite the existing efficient skill authoring standard. It complements it.

---

## 5. Required Professional Content Layers

A skill's professional content must exist across four layers.

### 5.1 Declared Professional Responsibility

Every skill must declare the work it professionally owns.

Required fields:

```text
professional_scope
owned_decisions
non_owned_decisions
primary_failure_risk
expected_professional_output
```

The declaration must be specific enough that a reviewer can tell whether the skill is too broad, too narrow, or misnamed.

Good:

```text
Own backend implementation and review decisions that affect service behavior, trust boundaries, consistency, idempotency, error semantics, async execution, and backend placement.
```

Bad:

```text
Help write better backend code.
```

### 5.2 Judgment Axes

Every skill must list the expert judgment dimensions required by its scope.

A judgment axis is not a checklist item. It is a professional lens that changes decisions.

Examples:

```text
- ownership boundary
- contract compatibility
- data consistency
- side-effect safety
- idempotency and retry behavior
- testability seam
- release and rollback exposure
- observability and diagnostic usefulness
```

Each judgment axis must answer:

```text
What decision can change if this axis is present?
What evidence is needed?
What failure does this prevent?
```

### 5.3 Decision Rules

A professional skill must contain ordered decision rules.

A decision rule must be:

- scoped to the skill;
- evidence-based;
- action-changing;
- testable or reviewable;
- connected to a failure mode, boundary, validation need, or handoff.

Good:

```text
If a retry path can duplicate side effects, define idempotency key scope before implementation and require a duplicate-delivery validation case.
```

Bad:

```text
Handle retries carefully.
```

### 5.4 Closure Contract

A skill must define what professional closure means.

Closure requires:

```text
selected professional mode
inspected boundaries
decision made
evidence collected
evidence limits named
validation result or not-verified status
residual risk
next gate or no-next-gate rationale
```

The skill must not allow closure through final prose alone.

---

## 6. Professionalism Requirements by Skill Type

### 6.1 Professional Skills

Professional skills are top-level task owners, reviewers, gates, or orchestrators. Their professional standard is highest.

A professional skill must include:

1. Declared owner/reviewer/gate role.
2. Task or work-surface ownership.
3. Expert judgment axes for the owned surface.
4. Mode-specific decision criteria.
5. Material hidden risks.
6. Failure modes with consequences.
7. Evidence contract strong enough for handoff.
8. Validation semantics.
9. Residual-risk handling.
10. Adjacent-skill handoff rules.

A professional skill fails professionalism review if it only describes workflow sequencing without professional judgment.

### 6.2 Foundation Capabilities

Foundation capabilities are narrow reusable professional fragments. Their professionalism is measured by focus and fragment quality.

A foundation capability must include:

1. One narrow decision responsibility.
2. Input fragment required from owner skill.
3. Decision rules specific to that responsibility.
4. Output fragment returned to owner.
5. Evidence required or produced.
6. Failure mode prevented.
7. Conditions where the capability must not expand scope.
8. Return-to-owner rule.

A foundation capability fails professionalism review if it becomes a broad top-level workflow, duplicates owner skill content, or returns final task output instead of a decision fragment.

### 6.3 Domain Extensions

Domain extensions add domain-specific risk and constraints to selected owner skills.

A domain extension must include:

1. Strong domain behavior signals.
2. Weak signal rejection.
3. Domain-specific professional judgment axes.
4. Domain-specific non-negotiable rules.
5. Domain risk escalation.
6. Domain validation addendum.
7. Domain residual risk.
8. Owner composition rule.

A domain extension fails professionalism review if it activates on keyword-only signals, replaces the professional owner, or claims domain safety/compliance without domain evidence.

---

## 7. Professional Content Quality Rules

### 7.0 Runtime-Facing Professional Actionability

Professional skills must expose judgment as executable runtime actions, not as
background expertise or generic advice. A selected skill should tell the agent
what to do first, when to stop, what evidence changes the decision, and what to
hand off next. This is the runtime expression of existing professionalism
dimensions: decision criteria, failure modes, the evidence contract, output
actionability, anti-patterns, and validation semantics.

A professional skill body or selected reference must make these action surfaces
clear:

- **First Moves** — the first inspected objects, files, contracts, examples,
  commands, or questions that establish the skill's owned boundary before
  planning or editing.
- **Stop Conditions** — the missing facts, failed checks, safety boundaries, or
  conflicting evidence that require the agent to ask, reroute, repair, or return
  `needs_user_choice` instead of guessing.
- **Action-changing Decision Rules** — ordered if/then rules that change
  implementation, review, validation depth, handoff target, or residual-risk
  ownership.
- **Concrete Good/Bad Examples** — short examples showing the rejected behavior,
  why it fails, how to detect it, and the professional replacement.
- **Agent-native Rationalizations** — common excuses an agent may use to close
  early, over-generalize, skip evidence, or treat prose as proof, paired with the
  required corrective action.
- **Minimal Verification Chain** — the smallest evidence path that can fail for
  the named risk, including what the validation proves, what it does not prove,
  and the residual risk when validation is not run.

Runtime-facing actionability does not add a third-language score, language
rubric, or style score. It is part of professional depth because it determines
whether the skill's judgment can be executed under real task pressure.

### 7.1 Specificity Rule

Professional statements must be concrete enough to change an action.

Reject:

```text
Use best practices.
Ensure quality.
Handle errors.
Add tests.
Consider security.
```

Prefer:

```text
If this changes an authorization query, inspect same-pattern permission filters and require at least one negative access test.
```

### 7.2 Consequence Rule

Every major professional rule should name the consequence it prevents.

Format:

```text
Rule: <decision or prohibition>
Prevents: <concrete failure>
Evidence: <how to prove or reduce risk>
```

### 7.3 Trade-Off Rule

Professional skills must define priority ordering when trade-offs conflict.

Examples:

```text
- Correctness before convenience.
- Public compatibility before internal elegance.
- Authorization safety before reuse.
- Behavior preservation before refactor aesthetics.
- Rollback ability before rollout speed.
- Evidence over assertion.
```

The ordering must be skill-specific. Generic priority slogans are insufficient.

### 7.4 Evidence Rule

A skill must distinguish evidence categories:

| Evidence class | Meaning |
|---|---|
| Strong evidence | source inspected, tests run, behavior reproduced, output captured |
| Medium evidence | static inspection, convention match, documented contract |
| Weak evidence | agent claim, unchecked checklist, inferred behavior |
| Missing evidence | required proof absent |
| Invalid evidence | proof unrelated to the risk being closed |

### 7.5 Validation Semantics Rule

Validation must map to the risk.

Bad:

```text
Run tests.
```

Good:

```text
Run the authorization regression test that proves cross-tenant access is denied. If no such test exists, state that permission isolation remains unverified.
```

### 7.6 Anti-Pattern Rule

A professional anti-pattern must include:

```text
wrong behavior
why it is wrong
how to detect it
professional replacement
```

Bad:

```text
Do not over-engineer.
```

Good:

```text
Wrong: create a new helper file for a one-call-site expression.
Why wrong: it increases navigation cost and hides ownership.
Detect: helper has one caller and no independent abstraction boundary.
Replacement: keep the logic near the owning function unless a second real caller or boundary emerges.
```

---

## 8. Professional Completeness Gates

Every skill must pass the following gates.

### 8.1 Scope Gate

```text
[ ] owned decisions are explicit
[ ] non-owned decisions are explicit
[ ] adjacent false positives are named
[ ] handoff target exists for non-owned work
```

### 8.2 Judgment Gate

```text
[ ] professional judgment axes are listed
[ ] each axis can change a decision
[ ] each axis has required evidence
[ ] each axis maps to a failure mode or quality risk
```

### 8.3 Failure Gate

```text
[ ] failure modes are skill-specific
[ ] failure modes include consequences
[ ] failure modes include detection or prevention
[ ] common shallow mistakes are rejected
```

### 8.4 Evidence Gate

```text
[ ] strong/weak/missing evidence are distinguished
[ ] evidence limits are required
[ ] final prose is not accepted as proof
[ ] residual risk must be named
```

### 8.5 Output Gate

```text
[ ] output tells the next actor what to do
[ ] output includes inspected boundaries
[ ] output includes validation or not-verified status
[ ] output includes residual risk
[ ] output includes next gate or no-next-gate rationale
```

---

## 9. Professional Anti-Patterns

Reject or rewrite skill content that:

- uses broad "best practices" language as a substitute for professional rules;
- has the same professional body as many adjacent skills with only names changed;
- lists risks without consequences;
- lists evidence without saying what it proves;
- requires validation without mapping validation to risk;
- closes with "looks good" or "implemented" without evidence;
- treats a foundation capability as a top-level owner;
- treats a domain extension as a standalone owner;
- confuses activation quality with professional depth;
- hides low professional content behind high reference precision;
- replaces expert judgment with workflow ceremony;
- contains long conceptual education but no decision rules;
- lacks trade-off priority;
- lacks residual-risk ownership;
- uses skill-specific terminology but no skill-specific decisions.

---

## 10. Required Report Separation

Reports must separate:

```text
professionalism_score
activation_quality_score
context_efficiency_score
runtime_benchmark_score
```

The professional score must be calculated only from professional content dimensions.

A release report may combine the four scores for readiness, but it must not present a single score as "professionalism" when that score includes routing, trigger, reference, or anti-bloat dimensions.

---

## 11. Definition of Done

A skill professionalism standard change is complete only when:

1. The skill's declared responsibility is explicit.
2. Professional judgment axes are present and skill-specific.
3. Decision rules are ordered, evidence-based, and action-changing.
4. Failure modes are concrete and consequence-bearing.
5. Evidence and validation semantics are tied to risk.
6. Anti-patterns include detection and replacement.
7. Residual risk and next gate are required.
8. Professionalism is reported separately from activation and context efficiency.
9. Benchmarks test professional obligations, not only prose format.
10. Regression governance prevents professional-depth loss during future efficiency edits.
