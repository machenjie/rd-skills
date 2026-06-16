# Changelog

All notable user-facing, contributor-facing, packaging, validation, and runtime artifact changes should be recorded here.

This project uses a simple release history format with an `Unreleased` section until maintainers publish versioned release notes.

## Unreleased

### Added

- Added `minimal-correct-implementation` foundation capability with routing,
  stage model, professional skill references, eval fixtures, and codegen
  benchmarks for minimal correct implementation, dependency avoidance,
  delete/shrink review, and shortcut ledger governance.
- Added first-stage optional ChangeForge Hook Runtime source, validation, build
  output, tests, and documentation for Codex and Claude project-level warning
  hooks.
- Added naming taxonomy, method placement, and naming-discipline routing
  coverage for implementation structure decisions.
- Added object-oriented structure thinking to `implementation-structure-design`, including object modeling, encapsulation, inheritance, composition, polymorphism, and object-versus-function decision gates.
- Added usage documentation for building, installing, invoking, upgrading, uninstalling, and troubleshooting ChangeForge runtime skills.
- Added open-source readiness documentation, contribution guidance, support policy, security policy, governance model, code of conduct, issue templates, pull request template, and CI validation workflow.

### Changed

- Clarified optional hook runtime repository boundaries, added hook manifest
  installation validation, and made hook behavior tests discoverable from the
  repository-level test command.
- Expanded `implementation-structure-design`, `language-idiom-enforcement`,
  `change-forge-router`, and AI review contracts so names are treated as
  ownership, responsibility, and boundary evidence.
- Expanded `implementation-structure-design` completion and escalation rules so object contracts, inheritance relationships, class hierarchies, and polymorphic interfaces are reviewed as structural and architectural decisions when applicable.
- Added project metadata links for homepage, documentation, issues, and source repository.

### Pending Maintainer Decision

- Select an OSI-approved license, add `LICENSE`, and update `pyproject.toml` license metadata before public open-source publication.
