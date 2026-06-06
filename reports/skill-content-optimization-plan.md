# Skill Content Optimization Plan

Derived from [`reports/skill-content-audit.md`](skill-content-audit.md) and governed
by [`docs/SKILL_CONTENT_GOVERNANCE.md`](../docs/SKILL_CONTENT_GOVERNANCE.md). This plan
sequences the optimization into risk-ordered phases. **P1, P2, and P3 are now
implemented**; the structural-slimming and capability-decomposition work that earlier
passes deferred has landed via reference decomposition and body tightening (no registry,
count, or profile change).

## Current Health Snapshot

| Kind | Count | Heavy | Notes |
| --- | --- | --- | --- |
| Professional skills | 19 | 0 over 350 lines | `change-forge-router` (215) is below the 220-line target; its Routing Result template now lives in `references/route-result-template.md` |
| Foundation capabilities | 104 | 0 over 250 lines | `implementation-structure-design` (237) and `ci-cd` (249) tightened under budget |
| Domain extensions | 7 | 0 over 300 lines | all within budget |

Professionalism is uniformly high: **0** skills fall below the professionalism gate, and
the three previously-thin foundation Quality Gates (`documentation-generation`,
`domain-logic-implementation`, `domain-object-identification`) now score 100 after being
rewritten as numbered verifiable checklists.

Suggested-action distribution: `KEEP_AS_IS` 130, `MERGE_DUPLICATE_CONTENT` 0,
`MOVE_SECTIONS_TO_REFERENCES` 0, `TIGHTEN_BODY` 0, `SPLIT_CAPABILITY` 0.

Top-level profile counts remain **recommended = 19, full = 26, dev = 130**.

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

## P2 — Reference splits (implemented)

### P2.1 `change-forge-router` — relocate route templates and manifest schemas (DONE)

- **Moved:** the two machine-readable manifest YAML schema blocks
  (`changeforge_route`, `changeforge_stage_route`) and their rules to
  `references/route-manifest.md`; the Markdown Routing Result template (sections 1-12,
  including `## 10. Quality Gates` and `## 12. Stage Professionalism`) to
  `references/route-result-template.md`.
- **Kept in body:** a compact Output Contract summary, the required section list, the
  manifest-consistency and skip-reason rules, and explicit pointers to both references.
  The risk triggers and Professional skill / Foundation capability / Domain extension
  routing blocks remain in body because they are runtime-critical routing selectors.
- **Validator change:** `validate-skill-body-links.py` parses Quality Gates from
  `references/route-result-template.md`; `validate-stage-routing-architecture.py` checks
  stage fields in the template/reference and only requires the router body to point to the
  template and name `changeforge_stage_route`.
- **Result:** router body 396 -> 215 lines. The `section_lines` exception was removed
  from `config/skill-content-exceptions.yaml`.

### P2.2 `change-intake-compiler` — summarize the template and deepen analysis (DONE)

- **Moved:** the Change Request Structure Template to
  `references/change-request-template.md`; the body points to it and enumerates the same
  fields in the Output Contract.
- **Added:** unimplementable-requirement detection, implicit non-goal identification,
  acceptance-signal reverse-derivation, and business-term glossary generation, plus a hard
  blocking-vs-non-blocking decision rule.
- **Result:** body 193 -> 169 lines.

### P2.3 `ci-cd` (foundation) — tighten body to budget (DONE)

- **Moved:** the illustrative gate-blocking decision tree to
  `references/pipeline-benchmarks.md` (its rule already lives in Non-Negotiable Rules);
  the three benchmark tables stay in the body so consumers keep them.
- **Result:** body 261 -> 249 lines (under the 250 budget).

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

## P3 — Capability decomposition (implemented via references)

### P3.1 `implementation-structure-design` (was 555 lines, now 237)

- **Approach taken — reference decomposition + body tightening (one capability, no
  registry/count/profile change):** `Critical Details` was reorganized into five
  decision-critical in-body subsections — `## Naming`, `## Reuse & Placement`,
  `## Object Modeling`, `## Placement Boundaries`, `## Shared-Utility Pollution` — each
  ending with a source/dev-only deep reference pointer for skill authors. The deep
  walkthroughs, decision trees, and record templates moved to five reference files:
  - `references/naming.md` (full naming taxonomy table),
  - `references/reuse-and-placement.md` (discovery protocol, reuse ladder, function tree),
  - `references/object-modeling.md` (object/method/class decision trees),
  - `references/placement-boundaries.md` (file/directory trees, FE/BE placement),
  - `references/advanced-refactoring.md` (extension safety + advanced refactor protocol).
- **Why references over a registry split:** `scripts/build.py` `_render_capability_reference`
  compiles a fixed set of capability **body** sections into each consuming professional
  skill, and does not copy a capability's own `references/` subfolder into consumers (those
  ship only in the `dev` whole-tree copy). Tightening the body is therefore what reduces
  compiled weight in `recommended`/`full`; the references serve the `dev` profile and skill
  authors. This keeps `EXPECTED_FOUNDATION_CAPABILITY_COUNT` at 104 and the dev profile at
  130 — no registry, `used_by`, routing-rule, or prose-count churn.
- **Result:** body 555 -> 237 lines (under the 250 budget); `split_candidate_score` cleared.

## P4 — Evidence-contract and stage-aware professionalism (implemented)

- **`agent-execution-discipline`** gained an `Evidence Contract Answer Set` (basis, files
  and boundaries inspected, placement rationale, validation commands, residual risk) and a
  Quality-Gate item enforcing it — the shared backbone for per-skill contracts.
- **17 of 19 professional skills** gained a tailored `## Evidence Contract` section (the
  router and intake compiler already carry equivalent machine-readable / pre-implementation
  contracts). **All 7 domain extensions** gained a domain-loss-path-specialized Evidence
  Contract.
- **Stage-aware language professionalism** was verified already present: all 8 language
  capabilities carry a five-stage `# Stage Fit` section (coding, debugging-diagnosis,
  code-review, refactoring, testing).
- **Golden cases:** added `evals/routing/go-backend-goroutine-leak-bugfix.yaml`, closing
  the Go-backend-bug-fix gap; the routing eval set is at 65 cases.

---

## P5 — Validator and guardrail enhancements

- **Implemented:** `scripts/audit-skill-content.py` (advisory report) and
  `scripts/validate-skill-content-size.py` (warning-only guardrail) with
  `config/skill-content-exceptions.yaml`; both wired into the
  [authoring workflow](../docs/USAGE.md#authoring-workflow).
- **Future:** the P2/P3 work has landed and the warn baseline is clean with no recorded
  content-size exceptions. Consider running the size validator with `--strict` in a CI
  gate so bodies cannot silently re-inflate. Do not enable `--strict` in CI until the
  exceptions list reflects every intended overage.

---

## Avoiding New Context Duplication

- Each moved block becomes a **skill-owned** reference (lives in that skill's folder);
  no shared, ownerless "common" reference is created.
- The body keeps only a summary plus a loading hint, so the full block is never loaded
  on a plain selection.
- The required, uniform `Reference Loading Policy` contract is left untouched — it is a
  deliberate shared contract enforced by `validate-skills.py`, not duplication to remove.
- Foundation capabilities keep decision-critical rules in the compiled body. Capability
  nested references such as `implementation-structure-design/references/*.md` are
  source/dev-only deep references for skill authors and the dev profile; they are not
  copied into recommended/full runtime skills, so the runtime reference model stays flat.
