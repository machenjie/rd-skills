# Skill Professionalism Evaluation and Governance Standard

Status: normative evaluation and release-governance standard  
Applies to: professionalism evaluation scripts, reports, benchmarks, baselines, and release readiness  
Primary goal: make professional depth measurable, regressions visible, and release decisions evidence-based

---

## Reader Path

- Start with [Purpose](#1-purpose) and [Current Reports And Quality Surfaces](#2-current-reports-and-quality-surfaces) to understand what each report proves.
- Use [Static Professionalism Evaluation](#3-static-professionalism-evaluation), [Regression Governance](#7-regression-governance), and [Release Readiness](#10-release-readiness) for maintainer decisions.
- Pair this document with [VALIDATION.md](../VALIDATION.md) before adding, renaming, or citing report artifacts.

## 1. Purpose

This standard defines how ChangeForge should evaluate and govern skill professionalism.

It separates four evaluation surfaces:

```text
professionalism_score
activation_quality_score
context_efficiency_score
runtime_benchmark_score
```

Only `professionalism_score` measures professional depth. Activation, routing, reference loading, and anti-bloat remain important, but they must not be counted as professional depth.

---

## 2. Current Reports And Quality Surfaces

The current executable report contract is produced by the commands in
[`../VALIDATION.md`](../VALIDATION.md). This standard defines the quality
surfaces those reports must keep separate; it does not introduce command names
that are not implemented in this repository.

Current reports:

```text
reports/skill-professionalism-eval.md
reports/skill-professionalism-eval.json
reports/skill-professionalism-depth.md
reports/skill-professionalism-depth.json
reports/professional-coverage-matrix.md
reports/professional-coverage-matrix.json
reports/professional-benchmarks-report.md
reports/professional-benchmarks-report.json
reports/professional-benchmarks-eval.md
reports/professional-benchmarks-eval.json
reports/professionalism-regression-report.md
reports/professionalism-regression-report.json
reports/professionalism-release-readiness.md
reports/professionalism-release-readiness.json
reports/skill-content-audit.md
reports/skill-content-audit.json
```

`skill-professionalism-eval` remains a compatibility report for the current mixed
static evaluation. `skill-professionalism-depth` is the professional-depth
report. `professional-coverage-matrix` covers key foundation and routing
coverage. `skill-content-audit` belongs to content-efficiency governance, not
professional-depth scoring.

Do not cite target names such as `skill-professionalism-release-readiness.*` or
`skill-professionalism-regression.*` as release evidence unless scripts generate
them. The current release evidence is `professionalism-release-readiness.*` and
`professionalism-regression-report.*`.

Recommended naming split:

| Current mixed concern | Recommended report |
|---|---|
| trigger/mode/stage | activation or routing quality |
| reference precision/body size | context efficiency |
| judgment/failure/evidence/output | professionalism depth |
| with-skill output delta | professional benchmark |

---

## 3. Static Professionalism Evaluation

Static evaluation checks authored content before runtime benchmarking.

### 3.1 Input files

Evaluate:

```text
src/professional-skills/*/SKILL.md
src/foundation/capabilities/*/SKILL.md
src/domain-extensions/*/SKILL.md
src/**/references/*.md
src/registry/*.yaml
evals/professional-benchmarks/**
```

### 3.2 Required output schema

Each evaluated item must include:

```yaml
name: string
path: string
kind: professional-skill | foundation-capability | domain-extension
professionalism_score: integer
status: sample-grade | release-grade | needs-review | weak | failing
dimensions:
  professional_responsibility_clarity: integer
  domain_judgment_depth: integer
  decision_criteria_completeness: integer
  failure_mode_specificity: integer
  evidence_contract_completeness: integer
  output_contract_actionability: integer
  boundary_and_ownership_precision: integer
  tradeoff_priority_quality: integer
  anti_pattern_quality: integer
  validation_semantics: integer
  residual_risk_handling: integer
warnings:
  - type: string
    severity: release-blocking | review-required | advisory
    message: string
    dimension: string
recommended_fixes:
  - string
```

### 3.3 What static evaluation may measure

Static evaluation may check:

```text
required sections
judgment-axis declaration
decision-rule presence
failure-mode structure
evidence contract fields
output contract fields
boundary/handoff language
anti-pattern quality structure
validation proof mapping
residual-risk fields
duplicate generic prose
domain-specific vocabulary coverage
skill-specific term coverage
```

### 3.4 What static evaluation must not overclaim

Static evaluation must not claim:

```text
the skill improves live agent behavior
the skill activates correctly
references load efficiently
the skill is professionally complete solely because sections exist
keywords prove deep professional judgment
all risks are covered
```

Static evaluation is a review aid. Benchmark evaluation is required for runtime-quality claims.

---

## 4. Professional Judgment Axis Registry

Every released professional skill and domain extension must have declared
professional judgment axes. The current registry is:

```text
docs/skill_professionalism_standard/professionalism-axes.yaml
```

This file is standard metadata for authoring evaluation. It is not a runtime
skill registry and must not be moved into `src/registry` or `src/toolbox`.

Evaluators use canonical `items.<name>` axes when present. Legacy `skills` and
`capabilities` buckets may be accepted by evaluators only as compatibility
fallbacks; new entries must use `items`.

If a professional skill, domain extension, key foundation capability, or
enhanced foundation capability falls back to generic default axes, the depth
evaluator emits a `missing_judgment_axes` warning. Non-key foundation
capabilities may use defaults unless they are promoted into the key foundation
or enhanced foundation set.

Rejected locations:

```text
src/registry/professionalism-axes.yaml
registry/toolbox.yaml
src/toolbox
```

Do not add user-specific archive, toolbox, or runtime content mappings to the
axis registry.

Example:

```yaml
items:
  backend-change-builder:
    axes:
      - service ownership boundary
      - authorization boundary
      - transaction consistency
      - idempotency and retry behavior
      - side-effect ordering
      - error contract
      - observability and diagnosis
      - placement and reuse rationale
      - release and rollback exposure
    required_minimum_axes: 7

  logging-design-gate:
    axes:
      - log purpose and consumer
      - severity semantics
      - structured fields
      - correlation and traceability
      - PII and secret redaction
      - sampling and cost
      - alert usefulness
      - incident diagnosis path
    required_minimum_axes: 6

  idempotency-retry-design:
    axes:
      - idempotency key scope
      - duplicate-delivery source
      - dedupe storage boundary
      - replay behavior
      - retry backoff
      - DLQ or fallback
      - validation case
    required_minimum_axes: 5
```

The evaluator should use this registry to avoid generic keyword scoring.

If a skill has no axis registry entry, it may still be evaluated, but it must receive a review-required warning unless it is explicitly exempt.

---

## 5. Failure Mode Catalog Requirement

Every professional skill and key foundation capability should declare a compact failure catalog.

Recommended structure:

```yaml
failure_modes:
  - id: duplicate_side_effect_under_retry
    condition: retry path can replay a side-effecting operation
    consequence: duplicate mutation, payment, job, entitlement, or external call
    detection: retry source exists and idempotency scope is undefined
    prevention: define idempotency key, dedupe store, and replay validation
    evidence: duplicate-delivery test or residual-risk disclosure
```

Static evaluation should check whether failure modes include:

```text
condition
consequence
detection
prevention_or_repair
evidence
```

A failure-mode list without consequences should not receive full credit.

---

## 6. Professional Benchmark Evaluation

Professional benchmarks prove whether the skill changes output quality, not just whether the file looks professional.

### 6.1 Case structure

Each case should contain:

```text
prompt.md
expected.yaml
baseline_output.md
with_skill_output.md
```

### 6.2 Expected fields

`expected.yaml` must include:

```yaml
expected_stage: string
expected_professional_skill:
  - string
expected_capabilities:
  - string
expected_professional_axes:
  - string
expected_failure_modes:
  - string
expected_evidence:
  - string
expected_output_obligations:
  - string
forbidden_behaviors:
  - string
expected_with_skill_status: pass | fail
```

### 6.3 Benchmark assertions

A passing with-skill output must include:

```text
selected professional skill
selected mode or owner role
professional axes addressed
failure modes handled or ruled out
inspected boundaries
evidence gathered
what evidence proves
what evidence does not prove
validation result or not-verified status
residual risk owner
next gate or no-next-gate rationale
```

The with-skill output must not:

```text
close without evidence
use generic best-practice advice
skip material failure modes
claim validation without command/result/manual proof
load unrelated domain/capability content
replace owner/reviewer separation with self-review
```

### 6.4 Delta requirements

A comparison case passes only when:

```text
with_skill_score > baseline_score
with_skill_score covers all required core professional obligations
baseline_output demonstrates at least one forbidden or shallow behavior
professional_delta >= configured minimum
```

Recommended thresholds:

```text
with_skill_score >= 85%
baseline_score <= 35%
professional_delta >= 40 percentage points
```

---

## 7. Regression Governance

Professionalism regression checks must compare current scores against a baseline.

Current baseline:

```text
config/professionalism-baseline.yaml
```

Minimum baseline fields:

```yaml
schema_version: 1
generated_at: timestamp
global_thresholds:
  no_new_weak_professional_skill: true
  no_score_regression_more_than: 1.0
  no_professional_depth_score_regression_more_than: 1.0
  no_new_professional_depth_core_regression: true
  no_new_missing_judgment_axes: true
  no_new_missing_failure_modes: true
  no_new_missing_evidence_contract: true
  no_new_generic_best_practice_regression: true
professional_depth:
  items:
    skill-name:
      path: string
      kind: string
      professionalism_score: integer
      status: string
      judgment_axis_source: string
      judgment_axes_count: integer
      dimensions:
        domain_judgment_depth: integer
        decision_criteria_completeness: integer
        failure_mode_specificity: integer
        evidence_contract_completeness: integer
        output_contract_actionability: integer
      known_warnings:
        - message: string
          type: string
          severity: release-blocking | review-required | advisory
```

The baseline also keeps the older mixed professionalism and coverage fields:

```yaml
professional_skills:
  skill-name:
    path: string
    kind: string
    total_score: integer
    status: string
    known_warnings:
      - message: string
```

### 7.1 Release-blocking regressions

Block release when:

```text
professional skill drops below 85
key foundation capability or domain extension drops below release-grade in strict mode
any core dimension drops below minimum
new missing judgment axes
new missing failure modes
new missing evidence contract
new generic best-practice replacement of concrete rules
new benchmark quality failure
```

### 7.2 Review-required regressions

Require explicit release review when:

```text
professionalism score drops by 1-2 points but remains above threshold
non-core dimension regresses
anti-pattern quality weakens
trade-off priority weakens
residual-risk handling weakens
benchmark delta shrinks but remains passing
```

### 7.3 Advisory changes

Advisory only:

```text
wording cleanup with no dimension regression
reference relocation with professional content preserved
body tightening that keeps all judgment axes and failure modes
new examples that do not affect release surfaces
```

---

## 8. Interaction with Efficiency Governance

Efficiency improvements must not delete professional depth.

When optimizing a skill body:

```text
[ ] judgment axes remain in SKILL.md or explicitly referenced
[ ] critical failure modes remain visible or loadable
[ ] evidence contract remains complete
[ ] validation semantics remain risk-specific
[ ] anti-patterns are preserved or moved with load conditions
[ ] output contract remains actionable
[ ] professionalism score does not regress
```

Moving content to references is allowed only when:

```text
SKILL.md retains a 3-5 line professional summary
reference has Load When / Do Not Load When
reference is linked by a professional condition
professional benchmark still passes
static professionalism score is preserved
```

Efficiency edits must not turn professional content into vague summaries.

---

## 9. Implementation Guidance

### 9.1 Current implementation mapping

Current scripts map the quality surfaces as follows:

```text
scripts/eval-professional-benchmarks.py
scripts/eval-skill-professionalism.py
scripts/eval-skill-professionalism.py --coverage-matrix
scripts/validate-professionalism-regression.py
scripts/validate-professionalism-regression.py --strict
scripts/validate-professional-routing-coverage.py
scripts/audit-skill-content.py
scripts/validate-skill-content-size.py
```

Future script splits may separate activation quality, context efficiency, and
professional-depth regression into dedicated entrypoints. Until such scripts
exist, documentation must use the current commands above. The current regression
validator already loads `reports/skill-professionalism-depth.json`; do not treat
the depth report as advisory-only.

### 9.2 New evaluator behavior

The depth evaluator should:

1. Parse frontmatter and body.
2. Extract required sections.
3. Load professional axis registry.
4. Score each rubric dimension.
5. Detect generic professional substitutions.
6. Detect missing consequence-bearing failure modes.
7. Detect weak evidence contracts.
8. Detect output closure gaps.
9. Detect type-specific ownership violations.
10. Validate that cited score-model and axis-registry paths exist.
11. Write JSON and Markdown reports.
12. Return non-zero only in strict mode or regression validation.

### 9.3 Warning taxonomy

Use these warning types:

```text
missing_professional_responsibility
missing_judgment_axes
weak_domain_judgment_depth
weak_decision_criteria
missing_failure_modes
weak_failure_mode_specificity
weak_evidence_contract
weak_output_contract
weak_boundary_ownership
missing_tradeoff_priority
weak_anti_patterns
generic_best_practice_substitution
weak_validation_semantics
missing_residual_risk
owner_capability_confusion
domain_keyword_only_professionalism_gap
professional_depth_regression
```

### 9.4 Severity mapping

```text
release-blocking:
  missing owner responsibility
  missing judgment axes for professional skill
  missing failure modes
  missing evidence contract
  missing output contract
  professionalism score below release threshold

review-required:
  core dimension regression
  weak trade-off priority
  weak anti-pattern quality
  weak validation semantics
  benchmark delta shrinkage

advisory:
  wording clarity
  non-core dimension minor weakness
  reference relocation follow-up
```

---

## 10. Release Readiness

A release is professionally ready only when:

```text
all professional skills are release-grade or sample-grade
all key foundation capabilities are release-grade or sample-grade
all domain extensions are release-grade or sample-grade
professional skills, domain extensions, key foundation capabilities, and enhanced foundation capabilities use item-specific judgment axes
no release-blocking professionalism warnings exist
no release-blocking professional depth warnings exist
release-review-required depth warnings have explicit accepted release review decisions
professional benchmarks pass
professionalism regression passes
efficiency edits did not reduce professional depth
release report separates professionalism, activation, context efficiency, and benchmark scores
```

Readiness report must include:

```text
professionalism_depth_summary
professional_depth_warning_reconciliation
activation_quality_summary
context_efficiency_summary
benchmark_delta_summary
regression_summary
release_blockers
review_required_items
accepted_warnings
non_blocking_followups
```

---

## 11. Migration from Existing Mixed Evaluation

Migration happens in three phases. Phase 3 is active for the current validator:
depth reports are loaded by regression validation and release readiness.

### Phase 1: Report separation without behavior change

- Keep existing evaluator.
- Add `professionalism_depth` section to generated reports.
- Move trigger/reference/anti-bloat dimensions into separate grouped sections.
- Add warnings when a mixed score is displayed as professionalism.

### Phase 2: Add depth rubric and baselines

- Add dimension rubric.
- Add professional axis registry.
- Add failure mode structure checks.
- Add new JSON output.
- Create baseline from current release.

### Phase 3: Make depth regression enforceable

- Use `validate-professionalism-regression.py` and
  `validate-professionalism-regression.py --strict` as the current strict
  regression commands.
- Block release on core professionalism regressions.
- Require benchmark evidence for major professional content changes.
- Require explicit review for depth and skill-eval release-review-required warnings.

---

## 12. Required Commands

The canonical runnable command set lives in [`../VALIDATION.md`](../VALIDATION.md).
For professionalism governance, the current focused commands are:

```text
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/audit-skill-content.py
python3 scripts/validate-skill-content-size.py
```

Do not add non-existent command names to release checklists. If a future
depth-specific or activation-quality command is implemented, add it to
`VALIDATION.md` first, then update this standard and the release checklist.

---

## 13. Definition of Done

Professionalism governance is complete when:

1. Professional depth has its own rubric and score.
2. Trigger, reference, and anti-bloat metrics are no longer counted as professional depth.
3. Every professional skill has declared judgment axes.
4. Key foundation capabilities have narrow decision fragments.
5. Domain extensions prove strong-signal and weak-signal professionalism.
6. Static reports identify missing depth, not only missing sections.
7. Benchmarks compare professional obligations, not only prose format.
8. Regression baselines block professional-depth loss.
9. Efficiency edits cannot silently remove professional content.
10. Release readiness reports separate all quality surfaces.
