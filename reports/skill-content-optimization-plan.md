# Skill Content Optimization Plan

Derived from [`reports/skill-content-audit.md`](skill-content-audit.md) and governed
by [`docs/SKILL_CONTENT_GOVERNANCE.md`](../docs/SKILL_CONTENT_GOVERNANCE.md). This plan
sequences the optimization into risk-ordered phases. Only **P0/P1** are implemented in
this pass; **P2/P3** are documented for a later, separately-reviewed change.

## Current Health Snapshot

| Kind | Count | Heavy | Notes |
| --- | --- | --- | --- |
| Professional skills | 19 | 1 over 350 lines | `change-forge-router` (396) is the sole heavy skill |
| Foundation capabilities | 104 | 2 over 250 lines | `implementation-structure-design` (555), `ci-cd` (261) |
| Domain extensions | 7 | 0 over 300 lines | all within budget |

Professionalism is uniformly high: **0** skills fall below the professionalism gate,
so there is **no P0 rewrite work**. The corpus is professionally authored; the
opportunity is context efficiency, not professionalism.

Suggested-action distribution: `KEEP_AS_IS` 126, `MERGE_DUPLICATE_CONTENT` 0,
`MOVE_SECTIONS_TO_REFERENCES` 2, `TIGHTEN_BODY` 1, `SPLIT_CAPABILITY` 1.

Top-level profile counts must remain **recommended = 19, full = 26, dev = 130** through
every phase.

---

## P0 — Must-fix professionalism / correctness

**None.** No skill scored below the professionalism gate and no required section is
missing. Nothing in this phase.

---

## P1 — High-value context slimming (implemented this pass)

### P1.1 De-duplicate the `Solution Optimality Self-Check` block (8 professional skills)

**Skills:** `backend-change-builder`, `frontend-change-builder`,
`data-api-contract-changer`, `integration-change-builder`, `ai-code-review-refactor`,
`architecture-impact-reviewer`, `change-impact-analyzer`,
`reliability-observability-gate`.

Each carries a 29-35 line `## Solution Optimality Self-Check` block (Three-Challenge
Rule + a skill-tailored performance-dimension matrix + "Additional Professional
Considerations"). The block is always-loaded on every selection even though it is only
needed when the change touches a performance-sensitive path.

A key audit finding: `solution-optimality-evaluation` (capability 82) lists
`used_by: [reliability-observability-gate, backend-change-builder,
frontend-change-builder, low-level-systems-extension]`. So **5 of the 8** skills carry
the inline block but are **not** wired to the capability, meaning the compiled
`references/capabilities/82-solution-optimality-evaluation.md` is not generated for
them. Pointing the body at that compiled path is therefore unsafe for those 5, and the
inline matrices are skill-tailored (backend vs. frontend vs. contract differ), so the
generic capability would lose tailoring.

Per move-to-reference candidate:

- **Original section:** `## Solution Optimality Self-Check` (the full block).
- **Target reference path:** `src/professional-skills/<skill>/references/solution-optimality.md`
  — a **skill-owned** file (not shared, not ownerless). `scripts/build.py` copies
  skill-root `references/*.md` verbatim; only `references/capabilities/` is
  build-managed, so this is safe.
- **Why move:** ~30 always-loaded lines × 8 skills of on-demand depth; duplicated
  pattern; tailoring must be preserved, not collapsed into the generic capability.
- **Body summary retained (4-6 lines):** the Three-Challenge Rule as three one-line
  prompts, plus one line naming the performance dimensions to budget, plus a loading
  hint. Keeps the `## Solution Optimality Self-Check` heading for discoverability.
- **When the reference loads:** governed by the existing Reference Loading Policy —
  read when the change touches a performance-sensitive path (L2 selected capability or
  L3+). It is never default-loaded.

**Why classified MERGE not MOVE:** the body shrinks to a summary and the depth is
relocated; we deliberately keep **per-skill** references rather than one shared file to
avoid an ownerless dumping ground while still removing the always-loaded duplication.

**Anti-Examples tables are intentionally NOT moved.** They are ~10 lines (under the
14-line budget), high-signal, and live inline as quick reference. Moving a 10-line table
adds indirection for no context saving; governance only moves blocks past the budget.

**Files changed:** for each of the 8 skills — `SKILL.md` (block → summary) and a new
`references/solution-optimality.md`.

**Risk:** low. No required section removed; no registry/`used_by`/routing change; no
build-managed path touched; backtick links in the summary (`solution-optimality-evaluation`)
resolve to a real capability and the section is not body-link-validated.

**Validation:**

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-skill-body-links.py
python3 scripts/audit-skill-content.py
python3 scripts/validate-skill-content-size.py
python3 scripts/build.py --profile recommended
python3 scripts/validate-installation.py
```

Expected after P1.1: the 8 `duplicate_block` warnings clear; the 8 skills drop ~24
lines each; profile counts unchanged.

---

## P2 — Reference splits (documented, not implemented this pass)

### P2.1 `change-forge-router` — relocate the route-manifest Output Contract

- **Original section:** `## Output Contract` (~141 lines, the machine-readable
  `changeforge_route` manifest example dominates it).
- **Target reference path:** `src/professional-skills/change-forge-router/references/route-manifest.md`.
- **Why move:** the router body is 349 lines; the verbatim manifest schema is reference
  material consulted when emitting the manifest, not contract a reader needs on every
  routing pass.
- **Body summary retained:** the manifest field list as a compact bullet list plus a
  pointer to the reference for the full example.
- **When the reference loads:** when the route actually emits a manifest (L2+).
- **Risk:** medium — `validate-skill-body-links.py` parses router-specific blocks
  (`Router quality gates`, risk triggers, routing blocks) out of the body. The Output
  Contract quality-gate list must remain in the body. Requires re-running
  `validate-skill-body-links.py` and `eval-routing.py`. Currently covered by a
  `section_lines` exception in `config/skill-content-exceptions.yaml`.

### P2.2 `change-intake-compiler` — summarize Industry Benchmarks

- **Original section:** `## Industry Benchmarks` (~52 lines).
- **Target reference path:** `src/professional-skills/change-intake-compiler/references/benchmarks.md`.
- **Why move:** Industry Benchmarks is a required section, but the deep standards list
  is appendix material; keep a 5-7 line summary in the body and move the catalog.
- **Body summary retained:** the named standards as a short list; deep notes in the
  reference.
- **When the reference loads:** L3+ or when the intake explicitly maps to a standard.
- **Risk:** low.

### P2.3 `ci-cd` (foundation) — tighten body to budget

- **Action:** `TIGHTEN_BODY`. Trim restating prose in the 261-line capability toward
  the ≤ 250 budget; this capability is a compiled reference, so brevity reduces compiled
  weight in every skill that uses it.
- **Risk:** low. Currently covered by a `body_lines` exception.

### P2.4 Foundation Industry-Benchmarks watchlist (optional tightening)

`error-code-design` (103), `degradation-circuit-breaking` (101),
`domain-event-modeling` (86), `form-validation-design` (86),
`idempotency-retry-design` (83), `concurrency-control` (81) each carry an
80-100+ line Industry Benchmarks section. These are **acceptable within the reference
budget** (overall bodies < 250 lines and they are selectively-loaded references), so
they are KEEP_AS_IS today. They are a future tightening watchlist only — not scheduled
work. The size validator intentionally does **not** gate foundation section size for
this reason.

---

## P3 — Capability split (documented, plan-only, high risk)

### P3.1 `implementation-structure-design` (547 lines)

- **Symptom:** the heaviest capability; `Critical Details` alone is ~361 lines.
  `split_candidate_score` 71.
- **Option A — Tighten in place (preferred first step):** reduce `Critical Details` to
  the decision-critical rules and relocate worked walkthroughs into the capability's own
  prose; no registry change. Lower risk; do this before considering a split.
- **Option B — Split into focused capabilities (only if tightening is insufficient):**
  - Candidate split: `implementation-structure-design` (placement/boundary decision) +
    a new `implementation-structure-anti-patterns` (the deep catalog).
  - **Registry update:** add the new capability to `src/registry/capabilities.yaml`
    with a fresh `id`, `group`, `path`, `status`, `used_by`, `triggers`, `risk_notes`,
    `expected_outputs`; bump `EXPECTED_FOUNDATION_CAPABILITY_COUNT` in
    `scripts/validation_utils.py`.
  - **`used_by` migration:** copy the parent's `used_by` set to the new capability so
    every consuming professional skill compiles both references; verify via
    `build.py` that `references/capabilities/` reflects both.
  - **Runtime profile impact:** `dev` top-level count rises by 1 (130 → 131);
    `recommended`/`full` top-level counts are **unchanged** (capabilities are references
    there). Update `EXPECTED_PROFILE_TOP_LEVEL_COUNTS` and the prose counts in
    `docs/RUNTIME_PROFILES.md`, `docs/USAGE.md`, and `docs/OPERATING_MODEL.md`.
- **Risk:** high — touches the registry, the enforced capability count, and the dev
  profile. Must be a standalone, separately-reviewed change. Currently covered by a
  `body_lines` exception.

---

## P4 — Validator and guardrail enhancements

- **Implemented this pass:** `scripts/audit-skill-content.py` (advisory report) and
  `scripts/validate-skill-content-size.py` (warning-only guardrail) with
  `config/skill-content-exceptions.yaml`; both wired into the
  [authoring workflow](../docs/USAGE.md#authoring-workflow).
- **Future:** once P2/P3 land and the warn baseline is clean, consider running the size
  validator with `--strict` in a CI gate so bodies cannot silently re-inflate. Do not
  enable `--strict` in CI until the exceptions list reflects every intended overage.

---

## Avoiding New Context Duplication

- Each moved block becomes a **skill-owned** reference (lives in that skill's folder);
  no shared, ownerless "common" reference is created.
- The body keeps only a summary plus a loading hint, so the full block is never loaded
  on a plain selection.
- The required, uniform `Reference Loading Policy` contract is left untouched — it is a
  deliberate shared contract enforced by `validate-skills.py`, not duplication to remove.
- Foundation capabilities are not given a nested reference layer; their lever is
  tightening or splitting, keeping the reference model flat.
