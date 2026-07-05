# Foundation Capability Authoring Standard

Status: normative overlay  
Version: v2  
Extends: ChangeForge Skill Authoring Base Standard  
Applies to: `changeforge_kind: foundation-capability`  
Role: narrow professional support capability, usually compiled into professional skill references

---

## 1. Purpose

Foundation capabilities are narrow decision modules. They support professional skills and return fragments.

A foundation capability must not:

- own full task execution;
- replace professional owner skills;
- independently close ordinary engineering work;
- route the entire task;
- become a mini professional skill.

It must:

- define one narrow decision;
- state compatible owner skills;
- require an input fragment;
- return an output fragment;
- return control to the owner skill.

---

## 2. Registry Contract

Every capability must appear in `src/registry/capabilities.yaml`.

Required fields:

```yaml
id: "05"
name: acceptance-standard-definition
group: intake-requirements
path: src/foundation/capabilities/acceptance-standard-definition
status: implemented
used_by: [acceptance-criteria-builder, quality-test-gate]
triggers: [...]
risk_notes: [...]
expected_outputs: [...]
```

Rules:

- `id` is stable.
- `used_by` is non-empty.
- `triggers` are selection signals, not generic labels.
- `risk_notes` state failure risk.
- `expected_outputs` describe a fragment.

---

## 3. Required Frontmatter

```yaml
---
name: acceptance-standard-definition
description: Use this capability when a selected owner skill needs focused rules for verifiable completion standards and rejecting vague acceptance language.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "05"
changeforge_version: 0.1.0
metadata:
  changeforge.skill_type: foundation-capability
  changeforge.capability_group: intake-requirements
---
```

Description must start with `Use this capability when `.

Budget:

```text
target: 160-320 chars
warning: >360
fail unless exception: >450
```

---

## 4. Required Section Order

```text
1. Mission
2. Capability Boundary
3. Load When
4. Do Not Load When
5. Used By / Owner Skill Compatibility
6. Required Input Fragment
7. Decision Rules
8. Critical Gotchas
9. Reference Loading Policy
10. Output Fragment
11. Evidence Requirement
12. Return To Owner Skill
13. Completion Criteria
```

All sections are required.

---

## 5. Mission

Mission must describe one focused capability.

Good:

```text
Define idempotency and retry decisions for retryable side-effectful operations.
```

Bad:

```text
Improve backend reliability.
```

---

## 6. Capability Boundary

Must state:

```text
what this capability decides
what it does not decide
which professional owner owns the broader task
adjacent capability boundaries
whether it is owner-scoped or route-level
```

---

## 7. Load When

Must contain strong selection signals.

Good:

```text
retry can duplicate side effects
queue redelivery exists
webhook replay is possible
dedupe key scope is unclear
```

Bad:

```text
reliability
backend
quality
```

---

## 8. Do Not Load When

Must reject:

```text
keyword-only matches
task outside used_by
owner skill not selected
output would duplicate another capability
capability would expand scope
professional owner can handle without this fragment
```

---

## 9. Used By / Owner Skill Compatibility

Must list compatible professional skills and use conditions.

Format:

```text
- backend-change-builder: when ...
- quality-test-gate: when ...
```

Do not select the capability for unlisted owners unless registry and evals are updated.

---

## 10. Required Input Fragment

Must specify the exact input needed from the owner skill.

If required input is missing, return a missing-input fragment rather than guessing.

Example fields:

```text
task intent
affected surface
selected owner skill
selected mode/stage
risk trigger
current behavior
desired behavior
validation target
material boundaries
```

---

## 11. Decision Rules

Rules must be ordered and testable.

Limit:

```text
5-12 rules in SKILL.md
larger matrices move to references
```

---

## 12. Critical Gotchas

Keep 3-5 capability-specific gotchas inline.

Do not duplicate broad professional gotchas.

---

## 13. Reference Loading Policy

Foundation capabilities should be light.

Default:

```text
L1: SKILL.md only
L2: one selected checklist/reference if needed
L3: one deep reference plus owner handoff
L4/L5: return to owner/gate for selected professional/domain references
```

If the capability has `references/`, it must have `references/index.md`.

---

## 14. Output Fragment

The output is never a final task result.

Required fields:

```text
capability
trigger_evidence
decision
required_controls
validation_or_evidence
residual_risk
return_to_owner
```

---

## 15. Evidence Requirement

Must state:

```text
what evidence is needed
what evidence proves
what evidence does not prove
what remains residual risk
```

Capability prose is not proof.

---

## 16. Return To Owner Skill

Must end with:

```text
Return to: <owner skill>
Owner must use this fragment to: <decision>
Do not close from this capability unless explicitly in dev authoring mode.
```

If no owner exists:

```text
blocked: missing owner skill selection
```

---

## 17. Capability Fragment Strictness

A foundation capability violates the standard if it:

- outputs a full route;
- closes ordinary engineering work;
- selects unrelated skills;
- writes task-level handoff as if it were a professional owner;
- contains a large professional workflow;
- has `Industry Benchmarks`, `Routing Coverage`, or `Proactive Triggers` that are not converted to fragment logic or moved to references.

---

## 18. Legacy Section Migration

When standardizing an existing capability, classify every old section:

```text
retain
merge into new section
move to references
delete
exception
```

Specific rules:

- `Industry Benchmarks` usually moves to `references/benchmarks-and-patterns.md`.
- `Proactive Professional Triggers` must become focused `Load When` / `Decision Rules` or move to references.
- `Routing Coverage` must become `Used By / Owner Skill Compatibility` or move out.
- `Failure Modes` may remain only if short and capability-specific.
- Long examples move to `examples/`.

---

## 19. Capability Size

```text
target body: 90-160 lines
review: >220
mandatory split/tighten: >250
```

If audit flags `TIGHTEN_BODY`, capability cannot be marked fully standardized without fix or exception.

---

## 20. Capability Evaluation

Required evals:

```text
selection by correct owner
not selected when unneeded
compiled reference loading
fragment quality
scope expansion rejection
```

Metrics:

```text
selected_by_correct_owner_rate
selected_when_required_rate
not_selected_when_unneeded_rate
fragment_assertion_pass_rate
scope_expansion_failure_rate
```

---

## 21. Capability Anti-Patterns

Reject if the capability:

- has no `used_by`;
- acts as standalone owner;
- has vague triggers;
- returns final task output;
- closes work alone;
- loads many references;
- duplicates professional body content;
- expands scope;
- cannot name its owner;
- keeps old professional-style sections without migration.

---

## 22. Capability Completion Gate

The capability is standardized complete only when:

```text
registry complete
section order valid
description within budget or exception
fragment output enforced
return to owner present
legacy sections migrated
references indexed if present
selection/reference/fragment/scope evals pass
```
