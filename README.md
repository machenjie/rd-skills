# ChangeForge Skill Mesh

ChangeForge Skill Mesh is a professional product-change engineering Skill system. It is designed for authoring, validating, building, packaging, installing, upgrading, and uninstalling ChangeForge skills across supported agent runtimes.

This repository is an authoring/build/install repository. Runtime skills are generated into `dist/` and installed from build outputs only. Source folders under `src/` are never installed directly.

ChangeForge is self-contained. It does not ingest, scan, index, summarize, map, package, or install any personal technical asset library. It does not create external asset mappings or assume user-specific knowledge sources are available at runtime.

## Why This Exists

General agent rules can remind an agent to be careful. ChangeForge turns that reminder into a routed engineering workflow: clarify requirements, inspect the target code before planning, define TDD or validation evidence, assign the right professional skill owner, run independent review, repair and re-review when needed, then hand off with evidence and residual risk.

## What Makes It Different

- It is not a prompt dump: `change-forge-router` selects skills, capabilities, and quality gates by change risk.
- It avoids context bloat: foundation capabilities are compiled into professional skill `references/` and loaded precisely by route.
- It is buildable and installable: runtime skills are generated into `dist/`, then managed by installers, doctor checks, and uninstall manifests.
- It is evidence-oriented: validation, eval, benchmark, example, and scorecard assets make the system auditable.
- It keeps runtime support in its lane: optional hooks, adapter protocol,
  repository graphs, project memory, validation broker, and trajectory inspector
  are bounded evidence helpers, not replacements for `change-forge-router` or
  direct source validation.

## One-Command Quickstart

```bash
python3 scripts/quickstart.py --agent codex --scope user
```

This builds the `recommended` profile, installs the built Codex user skills from
`dist/`, runs doctor, and prints a first prompt to try. For local dry-run review:

```bash
python3 scripts/quickstart.py --agent codex --scope user --dry-run
```

Use `recommended` for global installs, `full` for project installs that should expose domain extensions, and `dev` only when explicitly authoring/debugging ChangeForge. See [docs/QUICKSTART.md](docs/QUICKSTART.md) for Codex, Claude Code, GitHub Copilot, OpenAI API, and first-prompt examples.

Project-scope quickstart installs the non-executable route-preflight bootstrap
fragment by default. Executable hooks remain opt-in with
`--activation-level hooks` or `--activation-level professional-injection`.

## Usage

For day-to-day use, build a runtime profile, install the generated skills into the target agent runtime, then ask the agent to use the relevant ChangeForge skill for the change you are making.

Manual/debug path:

```bash
python3 scripts/build.py --profile full
python3 installers/install.py --agent copilot --scope user --profile full --dry-run
python3 installers/install.py --agent copilot --scope user --profile full
python3 installers/doctor.py --agent copilot --scope user --profile full
```

Use `recommended` for global installs, `full` for project installs that should expose domain extensions as top-level skills, and `dev` only for ChangeForge authoring/debugging. Project installs use `--target` as the target project root:

```bash
python3 installers/install.py --agent copilot --scope project --target /path/to/project --profile full
```

After installation, start with `change-forge-router` when the right workflow is unclear, or invoke a specific skill such as `frontend-change-builder`, `backend-change-builder`, `data-api-contract-changer`, `quality-test-gate`, or `delivery-release-gate` when the work is already scoped.

For engineering prompts in a target project, ChangeForge runtime use starts with
requirement clarification, then target-project code inspection before planning,
a TDD-oriented plan, action-specific skill ownership, independent review,
repair/re-review when findings exist, and evidence-based handoff with route
manifests. Pure explanation or translation prompts with no engineering action can
skip the full engineering flow after saying no engineering action is being taken.

See [docs/USAGE.md](docs/USAGE.md) for the full usage guide, including profile selection, agent-specific install examples, OpenAI API zip output, upgrade, uninstall, and authoring workflows.

## Professional Evidence

- [docs/BENCHMARKS.md](docs/BENCHMARKS.md): explains routing, professionalism, hook, profile, install, codegen, and optional Codex CLI live benchmark evidence.
- [reports/public-benchmark-summary.md](reports/public-benchmark-summary.md): generated public benchmark summary with known unknowns.
- [docs/SCORECARD.md](docs/SCORECARD.md): documents conservative scorecard dimensions and status rules.
- [docs/SCORECARD_DASHBOARD.md](docs/SCORECARD_DASHBOARD.md): generated human-readable scorecard dashboard.
- [docs/MARKETPLACE.md](docs/MARKETPLACE.md): describes the source-derived discovery index for skills, capabilities, and domain extensions.
- [docs/MARKETPLACE_CATALOG.md](docs/MARKETPLACE_CATALOG.md): generated local marketplace catalog for browsing skills, capabilities, gates, triggers, and profile exposure.
- [examples/README.md](examples/README.md): provides copyable engineering scenarios with expected routes and evidence.
- [docs/SHOWCASE.md](docs/SHOWCASE.md): scenario showcase comparing ordinary agent behavior against ChangeForge-routed behavior without requiring a demo repository.
- [docs/COMPARISON.md](docs/COMPARISON.md): positions ChangeForge against stable categories without live popularity claims.

## Current Evidence

These signals are generated or validator-backed local evidence, not external popularity, adoption, or marketplace-availability claims.

<!-- changeforge-scorecard-summary:start -->
| Evidence | Status | Source |
| --- | --- | --- |
| Profile build reproducibility | `pass` | [docs/SCORECARD_DASHBOARD.md](docs/SCORECARD_DASHBOARD.md) |
| Example coverage | `pass` | [scripts/validate-examples.py](scripts/validate-examples.py) |
| Codex CLI live pass-rate benchmark | `pass` | [reports/codex-live-benchmark-summary.json](reports/codex-live-benchmark-summary.json) |
| Codex CLI live capability coverage | `pass` | [reports/codex-live-benchmark-summary.json](reports/codex-live-benchmark-summary.json) |
| Marketplace index validation | `pass` | [scripts/validate-marketplace-index.py](scripts/validate-marketplace-index.py) |
| Open-source readiness | `partial` | [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md) |
<!-- changeforge-scorecard-summary:end -->

Stable profile counts are `recommended=21`, `full=28`, and `dev=163`; these generated manifests are the authoritative runtime profile count source. Local install starts with `python3 scripts/quickstart.py --agent codex --scope user`; official Codex/Claude marketplace publishing is intentionally not implemented.

Optional hook artifacts are also built for Codex, Claude Code, and GitHub
Copilot. They are execution reminders, not skills and not a replacement for
`change-forge-router`. See [docs/HOOKS.md](docs/HOOKS.md).

## Community And Governance

- [CONTRIBUTING.md](CONTRIBUTING.md): contribution workflow, validation commands, and pull request expectations.
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md): participation standards for maintainers, contributors, and users.
- [SECURITY.md](SECURITY.md): vulnerability reporting and security handling policy.
- [SUPPORT.md](SUPPORT.md): support channels and scope.
- [GOVERNANCE.md](GOVERNANCE.md): maintainer responsibilities, decision process, and release authority.
- [CHANGELOG.md](CHANGELOG.md): human-readable release history.
- [docs/OPEN_SOURCE_READINESS.md](docs/OPEN_SOURCE_READINESS.md): open-source readiness audit and remaining publication gates.

Before publishing this repository as open source, maintainers must choose an OSI-approved license, add the corresponding `LICENSE` file, and update the `pyproject.toml` license metadata. The repository currently records proprietary license metadata until that owner decision is made.

## Layers

ChangeForge has three authoring layers:

1. Professional Skills: top-level professional product-change skills with `SKILL.md` at runtime.
2. Foundation Capabilities: reusable engineering rules, benchmark names, selection criteria, and risk gates compiled into professional skill references.
3. Domain Extensions: optional domain-specific skills or references for full and development profiles.

## Runtime Outputs

Build outputs are written to `dist/`:

- `dist/universal/skills`: runtime-neutral skill folders.
- `dist/codex/project`: Codex project skill layout for `<target-repo>/.agents/skills`.
- `dist/codex/user`: Codex user skill layout for `~/.agents/skills`.
- `dist/codex/admin`: Codex admin skill layout for `/etc/codex/skills`.
- `dist/claude/project`: Claude Code project skill layout for `<target-repo>/.claude/skills`.
- `dist/claude/user`: Claude Code user skill layout for `~/.claude/skills`.
- `dist/copilot/project`: GitHub Copilot project skill layouts for `.github/skills`, `.agents/skills`, or `.claude/skills`.
- `dist/copilot/user`: GitHub Copilot user skill layouts for `~/.copilot/skills` or `~/.agents/skills`.
- `dist/openai-api/zips/<profile>`: OpenAI API hosted skill packages named `<skill-name>.zip`.
- `dist/codex/project/.codex`: optional Codex project hook runtime.
- `dist/claude/project/.claude`: optional Claude project hook runtime fragment and scripts.

## Runtime Profiles

- `recommended`: installs 21 professional skills as top-level runtime skills, with 135 foundation capabilities compiled into professional skill `references/`.
- `full`: installs 21 professional skills plus 7 eligible domain extensions as top-level runtime skills, with 135 foundation capabilities compiled into professional skill `references/`.
- `dev`: installs 21 professional skills plus 135 foundation capabilities plus 7 domain extensions as top-level runtime skills for authoring and validation work.

Recommended and full profiles must not install all foundation capabilities as top-level global skills. Foundation capabilities are compiled into professional skill references unless the `dev` profile is explicitly selected.

Runtime top-level counts are 21 for `recommended`, 28 for `full`, and 163 for `dev`.

## Reference Loading

`SKILL.md` is loaded when a skill is selected. The `references/` directory is not assumed to be fully loaded automatically. The router selects foundation capabilities, and professional skills read only selected capability references according to the L1/L2/L3/L4/L5 `Reference Loading Policy`.

References are a precision mechanism, not a dumping ground. Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.

## Guardrails

- Do not install `src/` directly.
- Do not install `src/registry` as runtime content.
- Do not create `src/toolbox`.
- Do not create `registry/toolbox.yaml`.
- Do not create or install personal asset mappings.
- Do not create language primers or beginner guides in `SKILL.md`.
- Runtime skills must be built into `dist/`.
- Installed skill folders must contain `SKILL.md` at their root.
- Generated files must be deterministic and reproducible.

## Validation

Use [docs/VALIDATION.md](docs/VALIDATION.md) as the canonical command set.
For fast governance checks, run:

```bash
python3 scripts/validate-src-invariants.py
python3 scripts/validate-skills.py
python3 scripts/validate-validation-broker.py
python3 scripts/validate-hooks.py
python3 scripts/validate-project-memory.py
python3 scripts/validate-skill-efficacy-benchmarks.py
```

Real local Codex CLI benchmark runs are opt-in. Strict comparative summaries
may borrow current Codex authentication, but must use temp `HOME`, hide
user-level skills/hooks/config/rules, pass `--ignore-user-config` and
`--ignore-rules`, and block publishing on baseline contamination. Current-home
full mode is documented as a separate smoke check in
[docs/BENCHMARKS.md](docs/BENCHMARKS.md) and does not feed public A/B claims.
Stronger local Codex evidence should use ablation mode across the publishable
assertion-backed cases with repeated runs; single-case runs remain smoke-scale
evidence.

`eval-skill-professionalism.py` writes both the main eval and key foundation coverage matrix;
`--coverage-matrix` writes only the coverage matrix reports for release checklist compatibility.

Run extended routing fixture comparison when updating or verifying captured
actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Star History

[![Star History Chart](https://api.star-history.com/chart?repos=machenjie/rd-skills&type=date&legend=top-left)](https://www.star-history.com/?repos=machenjie%2Frd-skills&type=date&legend=top-left)

## License Semantics

The repository tooling license is defined in `pyproject.toml` for the authoring, validation, build, packaging, and installer code. Runtime Skill frontmatter declares the license for each generated Skill independently. This split is intentional: repository/tooling policy and per-Skill runtime content policy are separate contracts, and build/install tooling preserves the per-Skill frontmatter instead of inheriting repository metadata.
