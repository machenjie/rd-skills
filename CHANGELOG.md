# Changelog

All notable user-facing, contributor-facing, packaging, validation, and built artifact changes should be recorded here.

This project uses a simple release history format with an `Unreleased` section until maintainers publish versioned release notes.

## Unreleased

### Added

- Added the authoritative `main-control-agent` prompt with Direct Task,
  Analyzed Work, First Executable Slice, preparation-loop breaker,
  isolation-aware scheduling, progress, review, repair, and re-review rules.
- Added four static Agent Profiles: main control, analysis, task, and review.
- Added Control, Professional, Foundation, and Domain registries with explicit
  triggers, anti-triggers, inputs, outputs, escalation, and targeted references.
- Added the first-phase coverage expansion: 2 Professional, 7 Domain, and 11
  Foundation Skills plus 63 new References. The same phase removes one obsolete
  preexisting mobile Domain, so the current Domain inventory is 13.
- Added the final Phase 2 inventory expansion: 2 Professional and 6 Foundation
  Skills, making the current source inventory 1 Control, 26 Professional, 150
  Foundation, and 13 Domain Skills: 190 total and 189 non-Control.
- Added Markdown contracts for Direct Tasks, Engineering Briefs, Task DAGs, and
  Review Handoffs.
- Added Hookless architecture, AI boundary, migration, benchmark, Marketplace,
  and build-profile documentation plus structural and deterministic validators.

### Changed

- Reorganized onboarding and reference documentation around reader goals,
  source-backed installation choices, copyable requests, recovery steps, and
  explicit evidence limits.
- Reworked all Professional Skills for AI execution with concise decision rules,
  high-value failure modes, stop conditions, output contracts, and selective
  Layer 3 loading.
- Changed `recommended`, `full`, and `dev` builds to standard Skill roots with
  27, 40, and 190 top-level Skills respectively, with 154/9, 141/9, and 0/0
  targeted/routing-only delivery.
- Changed normal Android and iOS/iPadOS routing to their successor Domains.
  Removed legacy Skill ids are unsupported and are not redirected.
- Changed the routing inventory to 233 canonical entries and 62 capability
  entries. Its 429 deterministic admissions are 105 Professional, 276
  Foundation, and 48 Domain admissions; the Foundation projection covers 141
  unique Foundation Skills in the 163-entry Layer 3 catalog.
- Classified the capability matrix: 125 entries classify as 81 covered, 39
  partial, 0 missing, and 5 intentionally unsupported. Partial entries use
  terminal `retain-partial` gap contracts rather than transitional evaluation
  dispositions.
- Changed routing and code-generation benchmark projections to select one Primary
  Professional Skill, zero to three Layer 3 Skills, and one Review Skill.
- Changed validation reports and code-generation command output to state their
  static, fixture, harness, and host/runtime evidence limitations.

### Removed

- Removed all Hook source, templates, installer flags, lifecycle integration,
  and Hook-specific tests.
- Removed task-context compilation, runtime dispatch, evidence storage, internal
  task identity, runtime schemas, phase state machines, and hidden role packs.
- Removed phase-specific and legacy worker Profiles in favor of the four static
  Profile model.
- Removed the obsolete `mobile-product-extension` Domain, its compatibility
  resolver and mode, and its legacy redirects, routes, fixtures, and
  current-state documentation.
- Removed the resource-intensive host-execution benchmark harness, its
  collection and release-gating workflows, and its generated summaries.

### License

- Selected MIT as the repository license, added root `LICENSE`, updated package metadata, and confirmed contribution/security readiness for public open-source publication.
