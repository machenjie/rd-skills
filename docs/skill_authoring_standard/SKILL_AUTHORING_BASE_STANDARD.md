# ChangeForge Skill Authoring Base Standard

Status: normative  
Version: v2  
Applies to: every ChangeForge skill-like unit, including professional skills, foundation capabilities, and domain extensions  
Primary goal: precise activation, low-cost `SKILL.md` loading, precise reference loading, measurable skill-only quality improvement

---

## Reader Path

- Start with [Purpose](#1-purpose), [Skill Type Model](#3-skill-type-model), and [Package Structure](#4-package-structure) for the baseline authoring contract.
- Use [Reference Architecture Standard](#11-reference-architecture-standard) and [Evaluation Standard](#17-evaluation-standard) when changing body/reference boundaries.
- Use the type-specific overlays for professional skills, foundation capabilities, and domain extensions after this base standard.

## 1. Purpose

This standard defines the universal authoring contract for efficient ChangeForge skills.

A ChangeForge skill is efficient only when:

1. The agent can decide whether to load it from `name` and `description`.
2. `SKILL.md` contains only always-needed activation-time guidance.
3. Deeper materials are loaded through explicit `references/`, `assets/`, and `scripts/` rules.
4. Adjacent skills have clear boundaries and do not steal context from each other.
5. The skill improves real task outcomes compared with no skill or the previous version.
6. The skill remains effective in skills-only mode; hooks may assist but must not be required for core behavior.
7. The skill is not merely structurally standardized; each section must be semantically useful.

---

## 2. Normative Basis

This standard is aligned with the Agent Skills model:

- A skill is a directory with a required `SKILL.md`.
- `SKILL.md` has YAML frontmatter followed by Markdown instructions.
- At discovery time, the system primarily sees `name` and `description`.
- After activation, the full `SKILL.md` is loaded.
- `references/`, `scripts/`, and `assets/` are optional resources loaded only when needed.
- `description` is the primary activation surface and must be evaluated with positive and negative prompts.
- Output quality must be evaluated by comparing without-skill and with-skill runs.
- Scripts must be non-interactive, self-contained, predictable, safe by default, and structured enough for agent use.

This standard is stricter than the generic format because rd-skills has many adjacent skills, compiled capability references, multiple runtime profiles, optional hooks, and professional engineering expectations.

---

## 3. Skill Type Model

The base standard applies to all skill types. A type-specific overlay must also apply.

| Skill type | `changeforge_kind` | Runtime role | Output shape |
|---|---|---|---|
| Professional skill | `professional-skill` | top-level owner, reviewer, gate, or orchestrator | task-level output |
| Foundation capability | `foundation-capability` | narrow support capability, usually compiled into professional references | output fragment |
| Domain extension | `domain-extension` | optional domain risk/constraint overlay | domain addendum |

Hard rule:

```text
Professional skills may own tasks.
Foundation capabilities return fragments.
Domain extensions return addenda.
```

A foundation capability must not silently become a mini professional skill. A domain extension must not replace the primary professional owner.

---

## 4. Package Structure

Every skill directory must follow this shape:

```text
skill-name/
  SKILL.md
  references/
  scripts/
  assets/
  evals/
```

Only `SKILL.md` is format-required, but every non-trivial skill must govern the optional directories.

### 4.1 `SKILL.md`

`SKILL.md` is the activation-time execution contract. It is loaded in full after activation. It must be compact, task-relevant, and free of low-frequency depth.

### 4.2 `references/`

`references/` contains deeper materials loaded by explicit conditions. References are precision mechanisms, not dumping grounds.

### 4.3 `scripts/`

`scripts/` contains non-interactive helpers for validation, transformation, checking, or generation.

### 4.4 `assets/`

`assets/` contains templates, schemas, example files, static resources, and large output formats.

### 4.5 `evals/`

`evals/` contains activation, output, reference-loading, trace, and composition evaluations.

---

## 5. Frontmatter Standard

Minimum required frontmatter:

```yaml
---
name: skill-name
description: Use this skill when ...
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---
```

### 5.1 `name`

Requirements:

- 1-64 characters.
- Must match the directory name.
- Lowercase letters, numbers, and hyphens only.
- No spaces, underscores, uppercase letters, leading/trailing hyphens, or consecutive hyphens.
- Must not be generic: avoid `general`, `helper`, `workflow`, `expert`, `misc`, `common`.

### 5.2 `description`

The description is the startup trigger. It must describe activation conditions, not summarize the entire skill body.

Required pattern by type:

```text
Use this skill when ...
Use this capability when ...
Use this domain extension when ...
```

A description must contain:

1. User/task intent.
2. Owned surface or narrow decision.
3. Key trigger signals.
4. High-risk or non-obvious activation cases.
5. Near-miss boundary where useful.

Forbidden patterns:

```text
Helps with ...
Useful for ...
General ...
All changes ...
Any code ...
Everything about ...
Best practices for ...
Catch-all ...
```

### 5.3 Description Startup Budget

Because descriptions are loaded before activation, they have a stricter budget than body text.

| Type | Target | Warning | Fail unless exception |
|---|---:|---:|---:|
| Professional skill | 220-360 chars | >360 | >450 |
| Foundation capability | 160-320 chars | >360 | >450 |
| Domain extension | 260-420 chars | >420 | >500 |
| Router/orchestrator | 260-420 chars | >420 | >520 |

Rules:

- Descriptions must be trigger conditions, not body summaries.
- A description may be long only when false-positive rejection requires it.
- Long descriptions require an exception with reason and `review_after`.
- The catalog total description budget must be tracked per profile.
- A release must not increase catalog startup token cost by more than 10% without activation precision/recall evidence.

### 5.4 Optional `compatibility`

Use only when environment assumptions materially affect use.

### 5.5 Optional `metadata`

Use namespaced metadata. Do not store secrets, raw prompts, private content, local absolute paths, personal archives, or hook state.

### 5.6 Optional `allowed-tools`

Use only when the target client supports it. Do not treat it as a universal security boundary.

---

## 6. Section Ordering Contract

Section order is a semantic dependency graph. It is not cosmetic.

Universal order:

```text
0. Frontmatter
1. Mission / Scope
2. Activation Boundary
3. Conflict Resolution
4. Required Context / Missing Information Policy
5. Critical Gotchas
6. Non-Negotiable Rules
7. Mode or Decision Selection
8. Risk Escalation
9. Reference Loading Policy
10. Execution Procedure
11. Output Contract
12. Evidence / Validation / Quality Gate
13. Handoff / Return / Escalation
14. Completion Criteria
```

Rules:

- Activation boundary must precede execution.
- Conflict resolution must precede reference loading.
- Required context must precede mode or decision selection.
- Mode/decision selection must precede reference loading.
- Reference loading must precede execution procedure.
- Output contract must depend on skill type and complexity.
- Quality gate must validate the output and evidence.
- Handoff must not create unowned work.

Type-specific standards may rename sections but must preserve the dependency order.

---

## 7. Section Semantic Quality Standard

A skill does not pass merely because required section headings exist. Each section must meet semantic minimums.

### 7.1 Mission / Scope

Must state:

- what the skill guarantees;
- the risk it prevents;
- the output it produces;
- what it does not replace.

### 7.2 Activation Boundary

Must state:

- direct triggers;
- implicit triggers;
- high-risk triggers;
- weak signals that are insufficient when relevant;
- explicit no-use conditions.

### 7.3 Conflict Resolution

Must state:

- when this skill is primary;
- when it becomes reviewer/gate/addendum only;
- at least the most likely adjacent false positives;
- when to hand off;
- when to skip this skill.

### 7.4 Required Context / Missing Information

Must state:

- required input/context;
- blocking unknowns;
- non-blocking assumptions;
- ask/block/proceed conditions.

### 7.5 Critical Gotchas

Must include 3-7 high-leverage, non-obvious gotchas that change first action or prevent material damage.

### 7.6 Non-Negotiable Rules

Must be specific, enforceable, and testable. Avoid slogans.

### 7.7 Mode or Decision Selection

Must choose a path before reference loading. Avoid large equal-option menus.

### 7.8 Reference Loading Policy

Must include:

- L1-L5 or equivalent complexity budget;
- selected references;
- forbidden/skipped reference rationale;
- trigger evidence requirement;
- reference budget;
- no “load all references” instruction.

### 7.9 Output Contract

Must match skill type:

- professional skill: task-level output;
- foundation capability: fragment;
- domain extension: addendum.

### 7.10 Quality Gate

Must be pass/fail, evidence-aware, and proportional to risk.

### 7.11 Handoff / Return / Escalation

Must name next owner/gate/reviewer and the evidence being handed off.

### 7.12 Completion Criteria

Must define the exact condition under which the skill’s role is complete.

---

## 8. SKILL.md Body Budget

| Skill type | Recommended body | Review threshold | Mandatory split threshold |
|---|---:|---:|---:|
| Professional skill | 180-220 lines | >250 | >300 |
| Foundation capability | 90-160 lines | >220 | >250 |
| Domain extension | 140-220 lines | >260 | >300 |
| Router/orchestrator | 180-240 lines | >260 | >300 |

Exceeding review threshold requires a tighten decision or recorded exception. Exceeding mandatory split threshold blocks “standardized complete” status unless the exception is justified by decision-critical content that cannot move to references.

---

## 9. Content Density Standard

Each paragraph must pass:

```text
Would the agent be significantly more likely to make a wrong decision without this paragraph?
```

Keep:

- project/domain-specific constraints;
- non-obvious gotchas;
- required ordering;
- default decisions;
- risk escalation;
- validation and evidence rules;
- reference loading triggers;
- concrete failure modes;
- handoff constraints.

Move to references:

- long tables;
- complete matrices;
- detailed checklists;
- full output schemas;
- long benchmark explanations;
- example catalogs;
- rare edge cases;
- detailed technology notes.

Delete:

- beginner tutorials;
- generic best practices;
- repeated “be careful” text;
- duplicated workflow text;
- tool-name lists without decision content;
- content already covered by a selected reference.

---

## 10. Critical Gotcha Exception

Critical gotchas must remain in `SKILL.md` when:

- the agent is unlikely to recognize the trigger;
- the error is common and high-impact;
- the gotcha changes the first action;
- missing it can cause security, data, release, compliance, financial, privacy, or irreversible damage.

Move gotchas to references only when:

- the trigger is obvious;
- the gotcha applies only to a narrow mode;
- `SKILL.md` explicitly says when to load that reference.

---

## 11. Reference Architecture Standard

### 11.1 Mandatory `references/index.md`

Any non-trivial skill with a `references/` directory must have:

```text
references/index.md
```

Required columns or equivalent structured fields:

```text
Reference
Load When
Do Not Load When
Depends On
Conflicts With
Max Level
Output Fragment
```

### 11.2 Reference Header

Every reference must start with:

```markdown
# Reference Title

## Load When
...

## Do Not Load When
...

## Inputs Expected
...

## Output Fragment
...
```

### 11.3 Chain Depth

Default allowed chain:

```text
SKILL.md -> references/index.md -> selected reference
```

Avoid:

```text
SKILL.md -> reference A -> reference B -> reference C
```

Reference chain depth must be <= 1 unless an exception is recorded.

### 11.4 Reference Selection Record

Every selected reference must have:

```text
reference_path
trigger_evidence
decision_supported
output_fragment_expected
why_adjacent_reference_skipped
```

### 11.5 Reference Budget

| Complexity | Reference limit |
|---|---:|
| L1 | 0-1 |
| L2 | 1-2 |
| L3 | 3-5 |
| L4 | 6-10 |
| L5 | 10-16 |

Exceeding budget requires explicit rationale.

---

## 12. Script Standard

Scripts must be:

- non-interactive;
- self-contained;
- safe by default;
- deterministic enough for agent use;
- structured in output;
- clear in error messages;
- idempotent or explicit about side effects;
- protected with `--dry-run` / `--confirm` for destructive operations.

Use scripts when:

- commands are fragile;
- outputs need parsing;
- validations are repeated;
- natural-language checking is unreliable;
- agents frequently make mistakes.

---

## 13. Output Contract Standard

Output contracts must be tiered and type-correct.

### 13.1 Compact

Default for L1/L2:

```text
mode/decision
selected owner/capability/extension
evidence required
references loaded/skipped
result or next action
residual risk
```

### 13.2 Standard

Default for L3:

```text
classification
context/assumptions
selected path
reference rationale
validation plan/result
review/repair status
residual risk
```

### 13.3 Full

Default for L4/L5 or explicit user request. Full templates belong in `assets/` or `references/`, not always-loaded body.

---

## 14. Bulk Skill Standardization Quality Standard

Bulk standardization is high risk because it can produce mechanical, malformed, or over-generalized sections.

After any batch update across multiple skills, inspect for:

1. broken sentences or residual fragments;
2. identical generic paragraphs across many skills;
3. “this skill”, “this file’s”, or “selected owner skill” boilerplate that hides real boundaries;
4. descriptions inflated into body summaries;
5. foundation capabilities becoming mini professional skills;
6. domain extensions becoming standalone task owners;
7. new sections that do not mention the skill’s actual domain;
8. duplicated old sections and new overlay sections;
9. reference policies that are generic and not tied to actual references;
10. examples or benchmarks retained in body without load rationale.

Recommended text-smell scan terms:

```text
re owns
this file's
this skill's surface
selected owner skill needs focused rules
broader implementation, review, release, or documentation work
Do not use it as a standalone owner
nearby material because it exists
```

A match is not automatically wrong, but requires review.

---

## 15. Legacy Section Migration Standard

When a skill is migrated to a new standard, every old section must be classified:

```text
retain in SKILL.md
merge into new section
move to references
delete
keep with exception
```

Rules:

- Foundation capabilities must migrate professional-style routing coverage into fragment-oriented rules or references.
- Domain extensions must migrate industry catalogs, risk matrices, and anti-examples into references unless they are short and always needed.
- Professional skills must not re-host full foundation capability bodies.
- Old sections are not grandfathered merely because they existed before.
- The migration PR or review must include an old-section-to-new-location map for broad migrations.

---

## 16. Type Weight Boundaries

### 16.1 Professional Skill

May be broad enough to own a task, but must not contain complete copies of all supporting capabilities.

### 16.2 Foundation Capability

Must be a narrow decision fragment. It must not own closure, route whole tasks, or produce full task output.

### 16.3 Domain Extension

Must be a domain addendum. It must not replace primary owner skill or close ordinary engineering work alone.

---

## 17. Evaluation Standard

### 17.1 Activation Eval

Datasets:

```text
train
validation
holdout
```

Each must include should-trigger and should-not-trigger prompts. At least 30% of negatives should be near-misses.

Metrics:

```text
activation_recall
activation_precision
false_positive_rate
false_negative_rate
near_miss_rejection_rate
confused_with_skill
multi_run_trigger_rate
```

### 17.2 Output Eval

Compare:

```text
without_skill
with_skill
with_skill_selected_references
previous_version
```

Metrics:

```text
assertion_pass_rate
pass_rate_delta
token_delta
duration_delta
reference_load_count
wrong_reference_load_count
missed_required_reference_count
```

### 17.3 Reference Loading Eval

Metrics:

```text
required_reference_hit_rate
forbidden_reference_avoid_rate
average_reference_count
reference_token_overhead
reference_confusion_pairs
```

### 17.4 Trace Review

Trace review must check whether the agent:

- activated the correct skill;
- skipped near-miss skills;
- loaded required references;
- avoided forbidden references;
- inspected source before planning when required;
- avoided full templates for low-risk tasks;
- validated or disclosed evidence limits;
- avoided relying on hooks for core skill behavior.

---

## 18. Skill Standard Completion Gate

A skill is not “standardized complete” until all four layers pass:

```text
structure pass
semantic pass
activation/reference/output eval pass
content efficiency pass
```

A skill cannot be marked complete when any of the following remain unresolved:

- description long-risk without exception;
- `TIGHTEN_BODY` finding without owner/plan;
- repeated phrase increase without rationale;
- generic reference loading policy;
- output contract does not match skill type;
- foundation capability returns full task output;
- domain extension returns standalone task output;
- no activation eval for high-use top-level skills;
- no reference-loading eval for reference-heavy skills;
- section contains broken text or template remnants.

---

## 19. Hook Boundary Standard

Hooks are runtime support, not skill capability.

Hooks may:

- inject concise context;
- observe bounded evidence;
- warn about stage/risk/closure;
- support CI/strict mode.

Hooks must not:

- replace skill content;
- require normal agents to inspect hook state;
- require agents to author internal protocol fields;
- make the skill ineffective without hooks.

Every skill must retain skills-only value.

---

## 20. Lifecycle Governance

Every skill change must declare:

```text
additive
tightening
split
merge
rename
deprecate
delete
reference-move
standardization-migration
```

Split/merge/rename/deprecate require migration notes and eval comparison.

---

## 21. Universal Checklist

```text
[ ] frontmatter valid
[ ] description trigger-first and within budget
[ ] section order valid
[ ] each section meets semantic minimum
[ ] no mechanical template remnants
[ ] critical gotchas inline
[ ] required context policy actionable
[ ] conflict resolution names real adjacent boundaries
[ ] references/index.md exists when references exist
[ ] reference load/no-load rules explicit
[ ] output contract matches skill type
[ ] old sections migrated or justified
[ ] activation/output/reference evals exist as required
[ ] trace review checks actual behavior
[ ] skill-only mode remains effective
[ ] completion gate satisfied
```
