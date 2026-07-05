# Documentation

Start here when you need the current documentation map for ChangeForge Skill Mesh. This page is hand-authored navigation; generated reports and catalogs are labeled below as snapshots.

## New Users

- [Quickstart](QUICKSTART.md)
- [Installation](INSTALLATION.md)
- [First prompts / Usage](USAGE.md)
- [Troubleshooting](USAGE.md#troubleshooting)

## Daily Users

- [Usage](USAGE.md)
- [Profiles](INSTALLATION.md#profiles)
- [Hooks](HOOKS.md)
- [Examples](../examples/README.md)

## System Model

- [Operating model](OPERATING_MODEL.md): source-vs-runtime boundary, routing flow, skill layers, hooks, telemetry, and reference loading.
- [Quality model](QUALITY_MODEL.md): L1-L5 risk levels and required evidence.
- [Engineering stage model](ENGINEERING_STAGE_MODEL.md): stage-specific capability launch, handoff, and evidence requirements.
- [Runtime profiles](RUNTIME_PROFILES.md): `recommended`, `full`, and `dev` profile composition.
- [Packaging](PACKAGING.md): OpenAI API zip contract, profile effects, and packaging guardrails.
- [Telemetry](TELEMETRY.md): fact-log boundaries, privacy guarantees, review, and human promotion.
- [Routing examples](ROUTING_EXAMPLES.md): examples for interpreting router output and evidence depth.

## Contributors

- [Contributing](../CONTRIBUTING.md)
- [Validation](VALIDATION.md)
- [Authoring workflow](USAGE.md#authoring-workflow)
- [Content governance](SKILL_CONTENT_GOVERNANCE.md)
- Skill authoring standards:
  - [Base standard](skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md)
  - [Professional skill standard](skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md)
  - [Foundation capability standard](skill_authoring_standard/FOUNDATION_CAPABILITY_AUTHORING_STANDARD.md)
  - [Domain extension standard](skill_authoring_standard/DOMAIN_EXTENSION_AUTHORING_STANDARD.md)
- Skill professionalism standards:
  - [Professionalism base standard](skill_professionalism_standard/SKILL_PROFESSIONALISM_BASE_STANDARD.md)
  - [Dimension rubric](skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md)
  - [Evaluation and governance](skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md)

`docs/skill_authoring_standard/` is the canonical source for skill shape,
activation, reference loading, and type overlays.
`docs/skill_professionalism_standard/` is the canonical source for
professional-depth scoring and regression governance.
`docs/SKILL_CONTENT_GOVERNANCE.md` governs body/reference layering, size,
duplication, and context efficiency.

## Maintainers

- [Release](RELEASE.md)
- [Benchmarks](BENCHMARKS.md)
- [Scorecard](SCORECARD.md)
- [Quality model](QUALITY_MODEL.md)
- [Professionalism release checklist](PROFESSIONALISM_RELEASE_CHECKLIST.md)
- [Professionalism enhancement standard](PROFESSIONALISM_ENHANCEMENT_STANDARD.md)
- [Professionalism enhancement matrix](PROFESSIONALISM_ENHANCEMENT_MATRIX.md)
- [Open Source Readiness](OPEN_SOURCE_READINESS.md)
- [License decision](LICENSE_DECISION.md)
- [Reports](../reports/README.md)

## Generated / Snapshot Docs

- [Scorecard Dashboard](SCORECARD_DASHBOARD.md): generated release snapshot from `reports/professional-scorecard.json`.
- [Marketplace Catalog](MARKETPLACE_CATALOG.md): generated local/source-derived discovery catalog only.
- [Marketplace](MARKETPLACE.md): local/source-derived discovery boundary and non-official marketplace status.
- [Showcase](SHOWCASE.md): generated scenario showcase from `examples/`.
- [Reports](../reports/README.md): generated validation, benchmark, and release-readiness snapshots.

## Reference And Comparison

- [Comparison](COMPARISON.md): category-level positioning without live market claims.

`docs/VALIDATION.md` is the canonical developer command set. Other documents should reference its Fast Source Invariants, Full Local, and [Release Gate](VALIDATION.md#release-gate) sections instead of copying long validation suites.

`docs/INSTALLATION.md` is the installation and hook behavior fact source. Other documents may summarize profile choice and hook defaults, but detailed install matrices, activation levels, upgrade, uninstall, doctor, and smoke checks belong there.
