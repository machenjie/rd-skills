# ChangeForge Skill Mesh

ChangeForge Skill Mesh is a professional product-change engineering skill system for authoring, validating, building, packaging, installing, upgrading, and uninstalling ChangeForge runtime skills.

This repository is a skill-authoring and release repository. Runtime skills are generated into `dist/` and installed from build outputs only; source folders under `src/` are never installed directly. ChangeForge does not ingest, scan, index, summarize, map, package, or install personal technical asset libraries, and it does not assume user-specific knowledge sources are available at runtime.

## Why This Exists

General agent rules can remind an agent to be careful. ChangeForge turns that reminder into a routed engineering workflow: clarify requirements, inspect the target code before planning, define TDD or validation evidence, assign the right professional skill owner, run independent review, repair and re-review when needed, then hand off with evidence and residual risk.

## What Makes It Different

- `change-forge-router` selects skills, capabilities, and quality gates by change risk.
- Foundation capabilities are compiled into professional skill `references/` and loaded by route, not dumped into every context.
- Runtime artifacts are generated into `dist/`, then managed by installers, doctor checks, uninstall manifests, and validation scripts.
- Hook runtime support provides bounded professional injection, gate reminders, and closure evidence checks; it does not replace `change-forge-router` or direct source validation.
- Generated examples, benchmark summaries, scorecards, and discovery catalogs are labeled as local evidence snapshots, not adoption or marketplace claims.

## One-Command Quickstart

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

For local dry-run review:

```bash
python3 scripts/quickstart.py --agent codex --scope user --dry-run
```

Supported Codex, Claude Code, and GitHub Copilot project/user quickstart and install paths enable the strongest supported hook/professional-injection mode by default. Use `--without-hooks` or `--activation-level none` to opt out. `--activation-level bootstrap` installs only the non-executable route-preflight fragment, and `--with-hooks` remains accepted as a backward-compatible legacy flag.

## Profiles

| Profile | Use | Top-Level Runtime Skills |
| --- | --- | ---: |
| `recommended` | Default user/global install. | 21 |
| `full` | Project install with domain extensions exposed. | 28 |
| `dev` | ChangeForge authoring and debugging only. | 164 |

Stable profile counts are `recommended=21`, `full=28`, and `dev=164`; these generated manifests are the authoritative runtime profile count source. Local install starts with `python3 scripts/quickstart.py --agent codex --scope user`; official Codex/Claude marketplace publishing is intentionally not implemented.

The profile composition is: `recommended` has 21 professional skills, `full` has 21 professional skills plus 7 domain extensions, and `dev` has 21 professional skills plus 136 foundation capabilities plus 7 domain extensions. Foundation capabilities are compiled into professional references for `recommended` and `full`.

## Documentation

Start with [docs/README.md](docs/README.md).

- [Quickstart](docs/QUICKSTART.md)
- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Hooks](docs/HOOKS.md)
- [Validation](docs/VALIDATION.md)
- [Release](docs/RELEASE.md)
- [Benchmarks](docs/BENCHMARKS.md)
- [Scorecard](docs/SCORECARD.md)
- [Open Source Readiness](docs/OPEN_SOURCE_READINESS.md)
- [Reports](reports/README.md)

`docs/INSTALLATION.md` is the detailed installation and hook behavior fact source. `docs/VALIDATION.md` is the canonical developer command set.

## Evidence

These signals are generated or validator-backed local evidence. They are not external popularity, official marketplace availability, or broad live-task success claims.

<!-- changeforge-scorecard-summary:start -->
| Evidence | Status | Source |
| --- | --- | --- |
| Profile build reproducibility | `pass` | [docs/SCORECARD_DASHBOARD.md](docs/SCORECARD_DASHBOARD.md) |
| Example coverage | `pass` | [scripts/validate-examples.py](scripts/validate-examples.py) |
| Codex CLI live pass-rate benchmark | `pass` | [reports/codex-live-benchmark-summary.json](reports/codex-live-benchmark-summary.json) |
| Codex CLI live capability coverage | `partial` | [reports/codex-live-benchmark-summary.json](reports/codex-live-benchmark-summary.json) |
| Marketplace index validation | `pass` | [scripts/validate-marketplace-index.py](scripts/validate-marketplace-index.py) |
| Open-source readiness | `partial` | [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md) |
<!-- changeforge-scorecard-summary:end -->

The marketplace index and catalog are local/source-derived discovery assets only. Official Codex/Claude marketplace publishing is intentionally not implemented.

## Community And Governance

- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow, boundaries, validation tiers, and pull request expectations.
- [GOVERNANCE.md](GOVERNANCE.md): maintainer responsibilities, decision process, and release authority.
- [SECURITY.md](SECURITY.md): vulnerability reporting and security handling policy.
- [SUPPORT.md](SUPPORT.md): support channels and scope.
- [CHANGELOG.md](CHANGELOG.md): human-readable release history.
- [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md): publication readiness audit and owner decision gates.

## License Semantics

The repository currently records proprietary license metadata. Before publishing it as open source, maintainers must choose an OSI-approved license, add the matching root `LICENSE`, update `pyproject.toml` license metadata, confirm contribution licensing, and confirm private vulnerability reporting or a private security contact path.

Repository/tooling license metadata and per-skill runtime frontmatter are separate contracts. Build and install tooling preserves each generated skill's runtime frontmatter instead of inheriting repository metadata.
