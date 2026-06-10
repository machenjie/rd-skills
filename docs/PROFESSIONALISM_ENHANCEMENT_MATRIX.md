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

| Stage | Owner capability(s) | Current coverage status | Enhancement / follow-up | Body or reference | Validation |
| --- | --- | --- | --- | --- | --- |
| requirement-intake | `requirement-clarification`, `acceptance-standard-definition`, `non-goal-boundary-definition` | implemented-with-known-warnings; needs-benchmark-coverage | Stage launch is wired via stage launcher; professional trigger hardening remains tracked in baseline/readiness. | body | `validate-capabilities`, `eval-routing`, `eval-skill-professionalism` |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation` | implemented-with-known-warnings; needs-benchmark-coverage | ADR rejected-alternatives and reversibility exist; architecture professional trigger hardening remains tracked. | body + per-skill `references/solution-optimality.md` | `validate-skill-body-links`, `eval-skill-professionalism` |
| implementation-planning | `implementation-structure-design`, `module-boundary-design`, `language-idiom-enforcement` | implemented-with-known-warnings | Reuse-priority and placement taxonomy exist; body-size exception remains tracked rather than hidden. | body (size exception tracked) | `validate-skill-content-size`, `audit-skill-content` |
| coding | language professional usage (`go`, `java-jvm`, `typescript`, `python`, `rust`, `cpp`, `shell-cli`, `sql`), `language-idiom-enforcement`, `input-validation` | needs-evidence-contract-hardening | Compact stage-differentiated `Stage Fit` block exists for all 8 language capabilities; key language capabilities remain `needs-review` in the coverage matrix. | body (compact) + capability body deep details | `validate-capabilities`, `validate-stage-routing-architecture`, `eval-skill-professionalism --coverage-matrix` |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` | implemented-with-known-warnings; needs-evidence-contract-hardening | Verified-cause and route-repair rules exist; `observability` remains `needs-review` in key foundation coverage. | body | `eval-routing`, `validate-professional-routing-coverage`, `eval-skill-professionalism --coverage-matrix` |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review` | implemented-with-known-warnings; needs-evidence-contract-hardening | Same-pattern scan and regression obligations exist; `regression-testing` remains `needs-review` in key foundation coverage. | body | `eval-routing`, `eval-skill-professionalism --coverage-matrix` |
| code-review | `code-review`, `ai-code-review-refactor`, `implementation-structure-design`, `language-idiom-enforcement` | implemented-with-known-warnings | AI review/refactor is sample-grade; `code-review` keeps a tracked body-table warning. | body | `validate-skill-body-links`, `eval-skill-professionalism` |
| refactoring | `refactoring`, `implementation-structure-design`, `regression-testing` | needs-evidence-contract-hardening | Behavior-preservation and characterization-test rules exist; `refactoring` and `regression-testing` remain `needs-review`. | body | `eval-routing`, `eval-skill-professionalism --coverage-matrix` |
| testing | `test-strategy`, `language-testing-strategy`, `unit-testing`, `integration-testing`, `contract-testing`, `e2e-testing`, `regression-testing`, `test-data-management` | needs-evidence-contract-hardening; needs-benchmark-coverage | Test-depth routing exists; multiple key testing capabilities remain `needs-review` pending evidence-contract hardening. | body | `validate-capabilities`, `eval-skill-professionalism --coverage-matrix` |
| release-delivery | `delivery-release-gate`, `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery` | implemented-with-known-warnings; needs-evidence-contract-hardening | Rollout/rollback/expand-contract rules exist; release readiness now blocks strict release while release-blocking accepted warnings remain. | body (ci-cd size exception tracked) | `validate-skill-content-size`, `validate-professionalism-regression --strict` |
| documentation-handoff | `documentation-generation`, `change-documentation-gate`, `agent-execution-discipline` | implemented-with-known-warnings; needs-benchmark-coverage | Documentation gate exists; proactive trigger hardening remains tracked in baseline/readiness. | body | `validate-skill-body-links`, `eval-skill-professionalism` |
| skill-authoring | `skill-authoring-expert` | needs-evidence-contract-hardening | Capability exists (id 103) and is referenced by the stage model and router stage routing; evidence contract remains `needs-review`. | body | `validate-stage-routing-architecture`, `eval-skill-professionalism --coverage-matrix` |

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
  review, refactoring, testing, release, and documentation were not broadly expanded in this rollout;
  remaining hardening is tracked through `reports/professional-coverage-matrix.*` and
  `reports/professionalism-release-readiness.*` instead of being hidden behind broad status labels.
- `skill-authoring-expert` was not recreated; it already exists (id 103) and is now referenced by
  the stage model and the router stage routing.
- The router and stage launcher were not given language-deep checklists; they reference the
  language capabilities instead (enforced by `validate-stage-routing-architecture`).
- Heavy detail already in references (`solution-optimality.md`, capability references) was left in
  place rather than promoted into bodies.

## Known Open Findings

The statuses above are intentionally conservative and must be read with the generated reports:

- `reports/professional-coverage-matrix.*` currently reports 29 key foundation capabilities, with
  22 still `needs-review`.
- `reports/skill-professionalism-eval.*` currently reports 21 professionalism warnings after the
  high-risk release-gate skills were hardened.
- `reports/professionalism-release-readiness.*` lists remaining known warnings and key foundation
  `needs-review` items as follow-ups, and blocks strict release while release-blocking accepted
  warnings remain in the baseline.

Body-size, duplication, and trigger-breadth findings remain governed by
[config/skill-content-exceptions.yaml](../config/skill-content-exceptions.yaml),
[reports/skill-content-optimization-plan.md](../reports/skill-content-optimization-plan.md), and
the release readiness checklist. They are not represented here as "none needed."

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
