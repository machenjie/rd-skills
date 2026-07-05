# Professional Skill Authoring Standard

Status: normative overlay  
Version: v2  
Extends: ChangeForge Skill Authoring Base Standard  
Applies to: `changeforge_kind: professional-skill`  
Role: top-level task owner, reviewer, gate, or orchestrator

---

## Reader Path

- Start with [Purpose](#1-purpose), [Required Frontmatter](#2-required-frontmatter), and [Required Section Order](#3-required-section-order) when authoring or reviewing a professional skill.
- Use [Mode Selection](#12-mode-selection), [Evidence Contract](#17-evidence-contract), and [Quality Gate](#18-quality-gate) when checking whether a skill can own work safely.
- Pair this overlay with the base authoring standard and content-governance document when moving content into references.

## 1. Purpose

Professional skills are top-level ChangeForge skills. They own, review, gate, or orchestrate engineering work.

A professional skill must:

1. Activate precisely from user task intent.
2. Own a clearly bounded engineering surface.
3. Resolve adjacent-skill conflicts.
4. Select minimum sufficient references and capabilities.
5. Compose with domain extensions only when strong domain signals exist.
6. Produce task-level output proportional to complexity.
7. Close or hand off with evidence and residual risk.
8. Remain useful without hooks.

---

## 2. Required Frontmatter

```yaml
---
name: backend-change-builder
description: Use this skill when implementing or reviewing backend behavior involving service logic, authorization, transactions, idempotency, retries, async jobs, error models, logging, or backend placement decisions.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
metadata:
  changeforge.profile: recommended
  changeforge.skill_type: professional
---
```

Description must start with `Use this skill when `.

Budget:

```text
target: 220-360 chars
warning: >360
fail unless exception: >450
```

---

## 3. Required Section Order

```text
1. Mission
2. Stage Ownership
3. When To Use
4. Do Not Use When
5. Adjacent Skill Conflict Resolution
6. Required Context / Missing Information Policy
7. Critical Gotchas
8. Non-Negotiable Rules
9. Mode Selection
10. Risk Escalation
11. Reference Loading Policy
12. Execution Procedure
13. Output Contract
14. Evidence Contract
15. Quality Gate
16. Handoff
17. Completion Criteria
```

All sections are required.

---

## 4. Mission

Mission must state:

- owned engineering surface;
- risk prevented;
- output produced;
- what it does not replace.

Good:

```text
Own backend implementation and review decisions affecting trust boundaries, consistency, idempotency, error semantics, async behavior, and backend placement.
```

Bad:

```text
Help with backend best practices.
```

---

## 5. Stage Ownership

Must specify:

- stages this skill can own;
- stages it can review;
- stages it gates;
- stages it must hand off;
- whether direct invocation skips router classification but still requires runtime prompt flow.

Allowed role terms:

```text
owner
reviewer
gate
orchestrator
handoff owner
```

---

## 6. When To Use

Must include:

- direct triggers;
- implicit triggers;
- high-risk triggers;
- evidence/repair triggers;
- stage triggers.

Each bullet should name behavior or surface, not generic quality.

---

## 7. Do Not Use When

Must name adjacent false positives.

Minimum:

```text
3 adjacent skill boundaries
1 skip condition
1 reviewer/gate-only condition
```

Example:

```text
Do not use this skill when API response shape, versioning, or DTO compatibility is primary; use data-api-contract-changer.
```

---

## 8. Adjacent Skill Conflict Resolution

This section must meet semantic minimums:

```text
- when this skill is primary owner
- when it becomes reviewer/gate only
- when adjacent skill owns the next action
- when domain extension adds addendum
- how to record skipped plausible skills
```

It must name actual adjacent skills. Generic text such as “prefer adjacent owner when stronger” is insufficient unless followed by concrete boundaries.

Forbidden quality issues:

```text
broken sentence fragments
placeholder-like references to "this file's"
generic "this skill's surface" without real surfaces
half-substituted trigger lists
```

---

## 9. Required Context / Missing Information Policy

Must include:

### Required context

```text
current behavior
desired behavior
non-goals
affected files/surfaces
owner module
validation signal
existing conventions
tests/config/docs
material data/API/security/release/domain boundaries
```

### Blocking unknowns

Ask/block when unknowns may change:

```text
public contract
data model
authorization
tenant behavior
migration/rollback
irreversible operation
domain semantics
release safety
```

### Non-blocking unknowns

Proceed only with explicit reversible assumptions.

---

## 10. Critical Gotchas

Keep 3-7 non-obvious gotchas inline.

Must include at least:

- first-action gotcha;
- evidence gotcha;
- placement or owner gotcha;
- reference-loading gotcha;
- closure gotcha.

---

## 11. Non-Negotiable Rules

Rules must be enforceable.

Good:

```text
Do not implement before inspecting owner surface and sibling conventions.
Do not close a bug fix without verified cause or same-pattern scan.
Do not use the same skill as owner and reviewer.
```

Bad:

```text
Write good code.
Be careful.
Consider risks.
```

---

## 12. Mode Selection

Must contain 4-8 modes.

Each mode must include:

```text
mode name
trigger signals
professional focus
required evidence
companion capabilities
skip by default
```

A full mode matrix longer than 50 lines must move to references.

---

## 13. Risk Escalation

Must define evidence-based escalation to:

```text
security-privacy-gate
data-api-contract-changer
data-middleware-change-builder
reliability-observability-gate
delivery-release-gate
quality-test-gate
domain extension
foundation capability
```

Keyword-only escalation is not enough.

---

## 14. Reference Loading Policy

Must include:

- L1-L5 budget;
- selected capability reference path format;
- when to load `references/capabilities/index.md`;
- when to load skill-owned references;
- when to load domain references;
- skipped-reference rationale;
- no load-all rule.

Required record per selected reference:

```text
reference_path
trigger_evidence
decision_supported
expected_output_fragment
why_not_adjacent_reference
```

---

## 15. Execution Procedure

Must be compact and action-oriented:

```text
1. Confirm role.
2. Classify missing context.
3. Inspect relevant source/test/config/docs.
4. Select mode and complexity.
5. Select references.
6. Execute or review.
7. Validate.
8. Handoff or close.
```

Do not force full process output for L1/L2.

---

## 16. Output Contract

Professional output is task-level.

### Compact L1/L2

```text
mode
role
source/tests to inspect or inspected
selected references
action/result
validation or not-verified risk
residual risk
```

### Standard L3

```text
classification
context
mode
impact
selected skills/capabilities/extensions
reference rationale
validation plan/result
review/repair status
residual risk
```

### Full L4/L5

Use full template only for high-risk, cross-surface, production, migration, security, financial, AI, Web3, or explicit user request.

---

## 17. Evidence Contract

Must distinguish proof from prose.

Strong evidence:

```text
source read
test read
diff
command output
review finding
re-review
runtime-observed bounded fact
```

Weak disclosure:

```text
agent final prose
self-review by owner
unsupported checklist claim
hand-authored protocol fields
```

---

## 18. Quality Gate

A professional skill passes only when:

```text
correct owner/reviewer/gate role
context sufficient or blockers handled
mode selected from evidence
reference loading minimal and justified
output tier proportional
validation evidence fresh or disclosed
residual risk named
handoff owner clear
skills-only behavior valid
```

---

## 19. Handoff

Must include:

```text
current skill role
next owner/reviewer/gate
mode
context inspected
selected references
validation evidence
unresolved findings
repair route
residual risk
```

---

## 20. Professional Body Efficiency

Professional skills must not re-host full foundation capability content.

Move to references:

```text
complete benchmark catalogs
large anti-example tables
full proactive trigger catalogs
full output schemas
long technical matrices
deep capability rules
```

If audit flags `TIGHTEN_BODY`, the skill cannot be marked fully standardized without a fix or exception.

---

## 21. Professional Evaluation

Required evals:

```text
activation
adjacent-conflict
output
reference-loading
trace
skills-only comparison
```

Must include cases where the skill is:

```text
primary owner
reviewer only
skipped in favor of adjacent skill
combined with domain extension
escalated to gate
compact only
```

---

## 22. Professional Anti-Patterns

Reject if the skill:

- acts as catch-all engineering expert;
- loads all capabilities;
- has long body-summary description;
- duplicates capability bodies;
- uses full output for L1/L2;
- lacks adjacent conflict details;
- produces process text instead of action;
- relies on hooks;
- uses same skill as owner and reviewer;
- contains template remnants or broken sentences.

---

## 23. Professional Completion Gate

The professional skill is standardized complete only when:

```text
required sections exist
section order valid
section semantic minimums met
description within budget or exception
no template remnants
body not flagged TIGHTEN_BODY unless exception
references/index.md exists if references exist
activation/conflict/output/reference/trace evals pass
```
