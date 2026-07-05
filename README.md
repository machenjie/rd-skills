# ChangeForge Skill Mesh

ChangeForge Skill Mesh is a professional product-change engineering skill system for authoring, validating, building, packaging, installing, upgrading, and uninstalling ChangeForge runtime skills.

## AI Transparency Without AI Interactivity

rd-skills is a one-way expert guidance system for AI agents. Hooks and skills may inject engineering judgment into agent context and observe bounded runtime facts, but normal engineering tasks must not require the agent to call rd-skills APIs, mutate hook state, repair runtime ledgers, or satisfy internal protocol fields. Strong evidence is captured from runtime-observed reads, edits, validations, reviews, and risk signals; AI-authored final text is weak disclosure only.

This repository is a skill-authoring and release repository. Runtime skills are generated into `dist/` and installed from build outputs only; source folders under `src/` are never installed directly. ChangeForge does not ingest, scan, index, summarize, map, package, or install personal technical asset libraries, and it does not assume user-specific knowledge sources are available at runtime.

## Why This Exists

General agent rules can remind an agent to be careful. ChangeForge turns that reminder into a routed engineering workflow: clarify requirements, inspect the target code before planning, define TDD or validation evidence, assign the right professional skill owner, run independent review, repair and re-review when needed, then hand off with evidence and residual risk.

## What Makes It Different

- `change-forge-router` selects skills, capabilities, and quality gates by change risk.
- Foundation capabilities are compiled into professional skill `references/` and loaded by route, not dumped into every context.
- Runtime artifacts are generated into `dist/`, then managed by installers, doctor checks, uninstall manifests, and validation scripts.
- Hook runtime support provides bounded professional injection, expert notes, automatic evidence observation, and closure quality reports; it does not replace `change-forge-router` or direct source validation.
- Generated examples, benchmark summaries, scorecards, and discovery catalogs are labeled as local evidence snapshots, not adoption or marketplace claims.

## Superpowers-Style Development Flow

ChangeForge absorbs the useful engineering discipline from Superpowers as
skill guidance, output contracts, validators, and evals. Ordinary agents see a
natural-language workflow:

1. Clarify the requirement.
2. Confirm the design.
3. Produce an executable Markdown implementation plan.
4. Execute one reviewable task at a time.
5. Validate each task.
6. Review spec compliance and code quality.
7. Repair important findings and re-review them.
8. Finalize with validation evidence and residual risk.

Ordinary agents are not asked to read or write internal task graphs, ledgers,
hook state, reducer facts, or metadata schemas. Maintainer, CI, benchmark,
doctor, and advisory hook tooling may derive bounded verification artifacts
from visible Markdown plans, but those artifacts are not part of the ordinary
agent workflow.

## One-Command Quickstart

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

For local dry-run review:

```bash
python3 scripts/quickstart.py --agent codex --scope user --dry-run
```

To remove a managed local install:

```bash
python3 installers/uninstall.py --agent codex --scope user --dry-run
python3 installers/uninstall.py --agent codex --scope user
```

Supported Codex, Claude Code, and GitHub Copilot project/user quickstart and install paths enable non-blocking expert advisor/professional-injection behavior by default. Strict block mode is reserved for explicit CI, benchmark, maintainer, or safety/permission boundaries. Use `--without-hooks` or `--activation-level none` to opt out. `--activation-level bootstrap` installs only the non-executable route-preflight fragment, and `--with-hooks` remains accepted as a backward-compatible legacy flag.

## Profiles

| Profile | Use | Top-Level Runtime Skills |
| --- | --- | ---: |
| `recommended` | Default user/global install. | 22 |
| `full` | Project install with domain extensions exposed. | 29 |
| `dev` | ChangeForge authoring and debugging only. | 165 |

Stable profile counts are `recommended=22`, `full=29`, and `dev=165`; these generated manifests are the authoritative runtime profile count source. Local install starts with `python3 scripts/quickstart.py --agent codex --scope user`; official Codex/Claude marketplace publishing is intentionally not implemented.

The profile composition is: `recommended` has 22 professional skills, `full` has 22 professional skills plus 7 domain extensions, and `dev` has 22 professional skills plus 136 foundation capabilities plus 7 domain extensions. Foundation capabilities are compiled into professional references for `recommended` and `full`.

## Documentation

Start with [docs/README.md](docs/README.md).

- [Quickstart](docs/QUICKSTART.md)
- [Installation](docs/INSTALLATION.md)
- [Usage](docs/USAGE.md)
- [Hooks](docs/HOOKS.md)
- [Validation](docs/VALIDATION.md)
- [Content Governance](docs/SKILL_CONTENT_GOVERNANCE.md)
- [Skill Authoring Standards](docs/skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md)
- [Skill Professionalism Standards](docs/skill_professionalism_standard/SKILL_PROFESSIONALISM_BASE_STANDARD.md)
- [Release](docs/RELEASE.md)
- [Benchmarks](docs/BENCHMARKS.md)
- [Scorecard](docs/SCORECARD.md)
- [Open Source Readiness](docs/OPEN_SOURCE_READINESS.md)
- [Reports](reports/README.md)

`docs/INSTALLATION.md` is the detailed installation and hook behavior fact
source. `docs/VALIDATION.md` is the canonical developer command set.
`docs/skill_authoring_standard/` owns how skills are authored;
`docs/skill_professionalism_standard/` owns professional-depth evaluation; and
`docs/SKILL_CONTENT_GOVERNANCE.md` owns body/reference layering and
content-efficiency governance.

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
| Open-source readiness | `pass` | [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md) |
<!-- changeforge-scorecard-summary:end -->

The marketplace index and catalog are local/source-derived discovery assets only. Official Codex/Claude marketplace publishing is intentionally not implemented.

## Community And Governance

- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow, boundaries, validation tiers, and pull request expectations.
- [GOVERNANCE.md](GOVERNANCE.md): maintainer responsibilities, decision process, and release authority.
- [SECURITY.md](SECURITY.md): vulnerability reporting and security handling policy.
- [SUPPORT.md](SUPPORT.md): support channels and scope.
- [CHANGELOG.md](CHANGELOG.md): human-readable release history.
- [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md): publication readiness audit and release validation gates.

## License

This repository is licensed under the MIT License; see [LICENSE](LICENSE).
Contributions are accepted under MIT unless maintainers document otherwise.

Repository/tooling license metadata and per-skill runtime frontmatter are separate contracts. Build and install tooling preserves each generated skill's runtime frontmatter instead of inheriting repository metadata.
