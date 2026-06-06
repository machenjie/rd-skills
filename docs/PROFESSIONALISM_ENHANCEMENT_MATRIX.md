# Professionalism Enhancement Matrix

This matrix records, per engineering stage, which capability owns the stage's professional
depth, what is already covered, what was enhanced in the stage-architecture rollout, whether the
detail lives in a SKILL body or a reference, and how it is validated. It is a review artifact, not
a runtime skill. The stage launcher (`engineering-stage-professionalism`) and the stage model
([docs/ENGINEERING_STAGE_MODEL.md](ENGINEERING_STAGE_MODEL.md)) drive which of these capabilities
launch for a given change.

Enhancement principle: enhance the owning capability for its stage only; do not copy depth across
capabilities, do not bloat bodies, and move long checklists, anti-examples, and benchmarks to
references.

## Stage Coverage Matrix

| Stage | Owner capability(s) | Current coverage | Enhancement applied | Body or reference | Validation |
| --- | --- | --- | --- | --- | --- |
| requirement-intake | `requirement-clarification`, `acceptance-standard-definition`, `non-goal-boundary-definition` | Strong (intake suite implemented) | None needed; stage launch wired via stage launcher | body | `validate-capabilities`, `eval-routing` |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation` | Strong | None needed; ADR rejected-alternatives and reversibility already present | body + per-skill `references/solution-optimality.md` | `validate-skill-body-links` |
| implementation-planning | `implementation-structure-design`, `module-boundary-design`, `language-idiom-enforcement` | Strong (547-line structure capability) | None needed; reuse-priority and placement taxonomy already present | body (size exception tracked) | `validate-skill-content-size` |
| coding | language professional usage (`go`, `java-jvm`, `typescript`, `python`, `rust`, `cpp`, `shell-cli`, `sql`), `language-idiom-enforcement`, `input-validation` | Strong per language | Added compact stage-differentiated `Stage Fit` block to all 8 language capabilities | body (compact) + capability body deep details | `validate-capabilities`, `validate-stage-routing-architecture` |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` | Strong (verified-cause, route-repair, same-pattern scan present) | None needed; language `Stage Fit` adds per-language debugging focus | body | `eval-routing` |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review` | Strong (same-pattern scan + regression required) | None needed | body | `eval-routing` |
| code-review | `code-review`, `ai-code-review-refactor`, `implementation-structure-design`, `language-idiom-enforcement` | Strong (severity/evidence/required-fix contract present) | None needed; language `Stage Fit` adds per-language review focus | body | `validate-skill-body-links` |
| refactoring | `refactoring`, `implementation-structure-design`, `regression-testing` | Strong (behavior preservation, characterization tests present) | None needed; language `Stage Fit` adds per-language refactoring focus | body | `eval-routing` |
| testing | `test-strategy`, `language-testing-strategy`, `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`, `test-data-management` | Strong | None needed; language `Stage Fit` adds per-language testing focus | body | `validate-capabilities` |
| release-delivery | `delivery-release-gate`, `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery` | Strong (rollout/rollback/expand-contract present) | None needed; depth stays in owning capability bodies/references | body (ci-cd size exception tracked) | `validate-skill-content-size` |
| documentation-handoff | `documentation-generation`, `change-documentation-gate`, `agent-execution-discipline` | Strong | None needed | body | `validate-skill-body-links` |
| skill-authoring | `skill-authoring-expert` | Strong (already implemented, id 103) | Not recreated; referenced by stage model and router routing | body | `validate-stage-routing-architecture` |

## Product Surface Ownership

Each product surface has an owning professional skill and matching capabilities; see the Product
Surface Selector in [docs/ENGINEERING_STAGE_MODEL.md](ENGINEERING_STAGE_MODEL.md). No product
surface is unowned. New product capability is added to the owning skill/capability, not to the
router or the stage launcher.

## Language Surface Ownership

Each of the 8 language surfaces has one owning capability and a compact `Stage Fit` block that
differentiates coding, debugging-diagnosis, code-review, refactoring, and testing concerns. Deep
per-language checklists stay in the owning language capability body; they are not copied into the
router, the stage launcher, or other capabilities.

## What Was Not Changed And Why

- Foundation capabilities for intake, architecture, implementation-planning, debugging, bug-fix,
  review, refactoring, testing, release, and documentation were already professionally complete;
  they were not expanded to avoid body bloat and duplication.
- `skill-authoring-expert` was not recreated; it already exists (id 103) and is now referenced by
  the stage model and the router stage routing.
- The router and stage launcher were not given language-deep checklists; they reference the
  language capabilities instead (enforced by `validate-stage-routing-architecture`).
- Heavy detail already in references (`solution-optimality.md`, capability references) was left in
  place rather than promoted into bodies.

## Known Open Findings

The "Strong / None needed" assessments above describe professional depth, not the absence of all
advisory findings. `scripts/audit-professionalism-coverage.py` is report-only and currently reports
**15 low-severity findings** (see [reports/professionalism-coverage.md](../reports/professionalism-coverage.md)).
They are accepted or deferred, not regressions:

- **body-size (3):** `change-forge-router` (396 lines), `ci-cd` (261), and `implementation-structure-design`
  (555) exceed the advisory body-line budget. Tracked in
  [config/skill-content-exceptions.yaml](../config/skill-content-exceptions.yaml); a capability split is
  documented as plan-only P3 in
  [reports/skill-content-optimization-plan.md](../reports/skill-content-optimization-plan.md). The
  compact `Stage Fit` blocks added to key capabilities add a few lines each but stay well inside the
  per-skill budget except for the already-tracked `implementation-structure-design`.
- **rule-duplication (11):** shared professional rule lines repeat across professional, capability, and
  domain-extension bodies. They are kept in-body deliberately so each skill stays self-contained when
  only its `SKILL.md` is loaded; consolidating into a shared reference is a deferred context-efficiency
  option, not a correctness fix.
- **trigger-breadth (1):** the `implementation-structure-design` routing trigger is one long string
  (107 words). It is deferred with the P3 split above; narrowing it without the split risks
  under-routing the structure capability.

The `skill-stage-declaration` findings previously reported here are resolved: every top-level
professional skill is now referenced in
[docs/ENGINEERING_STAGE_MODEL.md](ENGINEERING_STAGE_MODEL.md) (Stage Launch Matrix, Product Surface
Selector, or the Cross-Stage and Planning Professional Skills section). Re-run
`scripts/audit-professionalism-coverage.py` after authoring changes to refresh the count.

## Validation

- `scripts/validate-stage-routing-architecture.py`: stage model, stage launcher, router contract,
  stage route, and no language-deep copy into router/launcher.
- `scripts/audit-professionalism-coverage.py`: report-only coverage of stage/surface ownership,
  body size, duplicated rules, matrix duplication, trigger breadth, and output-contract
  verifiability. Writes `reports/professionalism-coverage.{md,json}`. Non-blocking unless `--strict`.
