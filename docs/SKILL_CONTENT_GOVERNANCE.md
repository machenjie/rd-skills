# Skill Content Governance

This document defines the content-layering standard for every ChangeForge
`SKILL.md` — professional skills, foundation capabilities, and domain extensions.
It exists so the skill mesh stays **precise, light, and correctly routable**: a
selected skill should load the decision-critical contract first, and reach deeper
material only when the change risk warrants it.

This is an authoring standard. It does not change runtime behavior, the build, the
installer, or the routing contract. It is enforced advisorily by
[`scripts/audit-skill-content.py`](../scripts/audit-skill-content.py) and, with a
warning-only default, by
[`scripts/validate-skill-content-size.py`](../scripts/validate-skill-content-size.py).

## Why This Exists

`SKILL.md` is loaded in full when a skill is selected. `references/` is **not**
assumed to be fully loaded — it is selectively read per the L1-L5
`Reference Loading Policy`. Therefore every line in a `SKILL.md` body is paid for
on every selection, while reference lines are paid for only when the route and risk
level call for them.

The governance goal follows directly: keep the **body** focused on the contract a
reader must have to act correctly and safely; push **depth, catalogs, and
appendices** into references where they are loaded on demand. References are a
precision mechanism, not a dumping ground, and not a default-loaded second body.

## Layering Standard

### 1. What the `SKILL.md` body should retain

The body is the always-loaded execution contract. It should keep:

- **Mission** — one paragraph: what this skill guarantees and why it matters.
- **When To Use / Trigger Signals** — concrete, routable entry conditions.
- **Do Not Use When** — explicit non-triggers and the adjacent skill to prefer.
- **Non-Negotiable Rules** — the hard rules that make the change safe.
- **Selection / Technical Selection Criteria** — the decision dimensions.
- **Risk Escalation Rules** — when to escalate and to whom.
- **Critical Details** — the 5-10 highest-leverage specifics, not an exhaustive list.
- **Reference Loading Policy** — the L1-L5 selective-loading contract (uniform, required).
- **Output Contract** — what the skill must return.
- **Quality Gate** — the verifiable pass/fail checks.
- **Handoff** — the next skills/capabilities.
- **Completion Criteria** — the definition of done.

### 2. What the body should not carry long-term

These belong in references once they grow past the thresholds below:

- Large anti-example tables.
- Large benchmark / standards catalogs.
- Multi-page deep checklists.
- Generic self-checks duplicated across many skills (e.g. the
  `Solution Optimality Self-Check` block).
- Long industry-background narration.
- Tool-name pile-ups with no decision content.
- Content already fully covered by a compiled foundation capability reference.
- Over-fine language-specific detail.
- Long risk matrices that only matter at L3/L4/L5.
- Specific case studies that only apply to a few scenarios.

### 3. What references should carry

- Extended checklists (`references/checklist.md`).
- Anti-example catalogs (`references/anti-examples.md`).
- Failure-mode catalogs.
- Deep decision tables and risk matrices.
- Worked examples (`references/examples.md`, `examples/`).
- Domain-specific and language-specific appendices.
- Migration / release / security deep-review detail.
- Skill-tailored deep method blocks such as a per-skill performance-dimension
  matrix (`references/solution-optimality.md`).

### 4. Foundation capabilities are compact decision aids

A foundation capability is a **compiled, selectively-loaded reference** in the
`recommended` and `full` profiles. It must read as a decision aid — rules,
selection criteria, failure modes, and a quality gate — not a full tutorial.
Because the capability is already a reference, the lever for an oversized
capability is **tightening the body** or **splitting into focused
sub-capabilities**, never adding a nested reference layer beneath it.

### 5. Professional skills orchestrate; they do not re-host capability bodies

A professional skill owns top-level orchestration and execution: routing,
impact, implementation guidance, gates, and specialist handoff. It must not paste
the full body of a foundation capability into itself. When it needs a capability's
method, it keeps a short summary in the body and relies on the compiled
`references/capabilities/<id>-<name>.md` (when the capability is wired through
`used_by`) or a skill-owned `references/*.md` file.

## Size And Duplication Thresholds

These thresholds are centralized in
[`scripts/audit-skill-content.py`](../scripts/audit-skill-content.py) (`THRESHOLDS`)
and mirrored by the size validator. Crossing a threshold is a **review signal**, not
an automatic defect — a skill may legitimately exceed one with a recorded exception.

| Signal | Threshold | Action |
| --- | --- | --- |
| Professional skill body | > 250 lines | Mark `review` (tighten) |
| Professional skill body | > 350 lines | Mark `heavy` (split/move) |
| Foundation capability body | > 250 lines | Mark `heavy` (tighten/split) |
| Domain extension body | > 300 lines | Mark `heavy` (move appendix) |
| Single section | > 80 lines | Split-reference candidate |
| Single table | > 20 rows | Move-to-reference candidate |
| Same paragraph in ≥ 3 skills | — | Common-reference / merge candidate |

## Scoring Model

The audit computes four advisory scores per skill. They are heuristic, transparent,
and never gate the build.

1. **`professionalism_score`** — explicit boundaries, concrete execution standards,
   a verifiable quality gate, measurable specifics (not vague prose), no
   tutorialization, and a verifiable output contract.
2. **`context_efficiency_score`** — body length within budget, no duplicated
   templates, low-frequency depth kept out of the body, no oversized tables, and no
   content that should live in references.
3. **`routing_clarity_score`** — clear `When To Use`, clear `Do Not Use When`, clean
   boundaries with adjacent skills, and low over-trigger risk.
4. **`split_candidate_score`** — body over the heavy threshold, multiple independent
   themes, oversized sections/tables, or mixed domains that argue for a split.

## Classification Taxonomy

Each skill is assigned one primary classification:

- **`KEEP_AS_IS`** — within size and professionalism budget.
- **`TIGHTEN_BODY`** — over the review/heavy gate; trim restating prose.
- **`MOVE_SECTIONS_TO_REFERENCES`** — has movable depth (anti-examples, benchmark
  lists, deep matrices) to relocate into `references/*.md`.
- **`SPLIT_CAPABILITY`** — a foundation capability doing too much; plan-only,
  high-risk, requires registry + `used_by` updates and profile re-validation.
- **`MERGE_DUPLICATE_CONTENT`** — carries a block duplicated across many skills;
  replace with a summary plus a reference pointer.
- **`REWRITE_FOR_PROFESSIONALISM`** — boundaries, standards, or quality gate are
  thin; fix before any move.
- **`DEFER`** — out of scope for the current pass.

## Move-To-Reference Rules

A move must preserve professional content. It is a relocation, never a deletion.

1. Keep a **3-5 line summary** of the moved block in the body.
2. Create a **skill-owned** reference file under that skill's `references/` (never a
   shared, ownerless dumping ground).
3. Point to it with a one-line **loading hint** tied to the change risk
   ("load when the change touches a performance-sensitive path").
4. The `Reference Loading Policy` continues to govern when the reference is read; the
   reference is never default-loaded.
5. `references/*.md` authored at the skill root are copied verbatim by
   [`scripts/build.py`](../scripts/build.py); only `references/capabilities/` is
   build-managed, so skill-owned references are safe to add.

## Invariants This Standard Must Not Break

- Source stays under `src/`; runtime is generated into `dist/` only.
- Professional skills remain the runtime top-level entry points.
- Foundation capabilities remain compiled references in `recommended`/`full`; they are
  **not** promoted to top-level skills there.
- Top-level skill counts stay fixed: `recommended` = 19, `full` = 26, `dev` = 131
  (19 professional + 105 foundation + 7 domain).
- References stay selectively loaded; nothing here makes them default-loaded.
- Required sections (per `validate-skills.py`, `validate-capabilities.py`,
  `validate-domain-extensions.py`) remain present; oversized **required** sections are
  shrunk to a summary, not removed.
- Backtick registry links in validated sections continue to resolve
  (`validate-skill-body-links.py`).
- No skill loses professional depth; depth is relocated, not dropped.

## Authoring Workflow Integration

When changing any `SKILL.md`, run the content audit and size check alongside the
existing validators:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-skill-body-links.py
python3 scripts/audit-skill-content.py          # advisory report, never fails
python3 scripts/validate-skill-content-size.py   # warning-only by default
```

The audit writes `reports/skill-content-audit.md` and
`reports/skill-content-audit.json`. The size validator warns when a body, section, or
table crosses a governance threshold without a recorded exception in
[`config/skill-content-exceptions.yaml`](../config/skill-content-exceptions.yaml).
Neither tool blocks the build; both are review aids that keep bodies from silently
re-inflating.
