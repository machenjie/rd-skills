# Release

This runbook covers ChangeForge skill system releases. Releases are cut from authored source, validated registries, generated `dist/` outputs, profile-scoped OpenAI API zips, and installer smoke evidence.

## Versioning

- Update `pyproject.toml` `[project].version` for repository release identity.
- Update `changeforge_version` in touched `SKILL.md` files when skill behavior changes.
- Preserve backward compatibility for registry fields, runtime folder names, and installer CLI flags unless a migration note is included.

## Build

Build every profile:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
```

Expected top-level runtime counts:

- `recommended`: 19 professional skills.
- `full`: 19 professional skills plus 7 domain extensions.
- `dev`: 19 professional skills plus 117 foundation capabilities plus 7 domain extensions.

Foundation capability count is 117 in every profile: compiled into professional references for `recommended` and `full`, and also top-level in `dev`.

The profile top-level counts are 19 for `recommended`, 26 for `full`, and 143 for `dev`.

## Package

OpenAI API zips are profile-scoped under `dist/openai-api/zips/<profile>`. Repackage a built profile when needed:

```bash
python3 scripts/package.py --profile recommended
python3 scripts/package.py --profile full
python3 scripts/package.py --profile dev
```

Each zip must contain exactly one top-level skill folder and exactly one root `SKILL.md`.

## Validation

Run the core validation suite before handoff:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/validate-examples.py
python3 scripts/validate-productization-assets.py
python3 scripts/audit-skill-content.py
python3 scripts/eval-routing.py
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/validate-hooks.py
python3 scripts/eval-pressure-behavior.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
python3 scripts/export-marketplace-index.py --profile recommended --out /tmp/recommended-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile full --out /tmp/full-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile dev --out /tmp/dev-marketplace-index.json
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
python3 scripts/generate-professional-scorecard.py --strict-profile-builds --out /tmp/professional-scorecard.md --json-out /tmp/professional-scorecard.json
```

Run extended routing fixture comparison when updating or verifying captured
actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

Run installer dry runs for supported targets:

```bash
python3 installers/install.py --agent codex --scope user --profile recommended --dry-run
python3 installers/install.py --agent codex --scope project --target /tmp/changeforge-codex-full --profile full --dry-run
python3 installers/install.py --agent claude --scope user --profile recommended --dry-run
python3 installers/install.py --agent claude --scope project --target /tmp/changeforge-claude-full --profile full --dry-run
python3 installers/install.py --agent copilot --scope user --profile recommended --dry-run
python3 installers/install.py --agent copilot --scope project --target /tmp/changeforge-copilot-full --profile full --dry-run
python3 installers/install.py --agent openai-api --profile recommended --dry-run
```

Run final smoke checks against disposable targets:

```bash
python3 installers/install.py --agent codex --scope user --target /tmp/changeforge-recommended-user-smoke --profile recommended
python3 installers/install.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --profile full
python3 installers/uninstall.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --dry-run
python3 installers/doctor.py --agent codex --scope user --target /tmp/changeforge-recommended-user-smoke --profile recommended
python3 installers/doctor.py --agent codex --scope project --target /tmp/changeforge-full-project-smoke --profile full
python3 installers/install.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --profile full
python3 installers/doctor.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --profile full
python3 installers/uninstall.py --agent claude --scope project --target /tmp/changeforge-claude-full-smoke --dry-run
python3 installers/install.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --profile full
python3 installers/doctor.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --profile full
python3 installers/uninstall.py --agent copilot --scope project --target /tmp/changeforge-copilot-full-smoke --dry-run
python3 installers/install.py --agent openai-api --profile recommended --dry-run
python3 scripts/validate-installation.py
```

The Codex recommended user smoke must install 19 top-level skills. The Codex, Claude Code, and GitHub Copilot full project smoke installs must each install 26 top-level skills. The Codex, Claude Code, and GitHub Copilot uninstall dry-runs must list only manifest-managed names. Doctor must pass for every installed smoke target. OpenAI API zip validation must pass profile count and archive shape checks.

## Release Checklist

- Source structure matches the registry counts.
- README, quickstart, examples, benchmark docs, scorecard docs, and marketplace docs pass productization validation.
- Open-source publication status has been checked against [OPEN_SOURCE_READINESS.md](OPEN_SOURCE_READINESS.md) when publishing publicly.
- License metadata, root `LICENSE`, contribution licensing, and security contact path are resolved before describing a release as open source.
- Routing and code generation benchmark validators pass.
- No banned `src/toolbox` or `registry/toolbox.yaml` path exists.
- No personal asset mapping, raw `src/`, or raw registry content is installed.
- All runtime skills contain root `SKILL.md`.
- Foundation capabilities are compiled into professional skill references for `recommended` and `full`.
- Professional skills load only selected references according to the L1/L2/L3/L4/L5 `Reference Loading Policy`; `references/` is not treated as automatic context.
- Installer dry runs show 19 skills for recommended and 26 for full project installs.
- Final smoke commands cover Codex user recommended install, Codex project full install, Codex project uninstall dry-run, Codex user/project doctor, Claude Code project full install/doctor/uninstall dry-run, GitHub Copilot project full install/doctor/uninstall dry-run, OpenAI API recommended zip dry-run, and installation artifact validation.
- OpenAI API zips pass profile count and archive shape validation.
- Professional scorecard is regenerated from current local evidence or explicitly marked as a sample snapshot.
- Marketplace index exports pass smoke checks for `recommended`, `full`, and `dev`.
- Showcase examples pass `python3 scripts/validate-examples.py`.
- Cloud component routing for Redis/Kafka/K8s/Helm/Spark remains covered by routing evals.
- Helm chart changes include lint/template/schema/rendered-manifest validation and secret values review.
- Docs reflect any CLI, packaging, profile, or installer behavior changes.
- Unresolved assumptions and manual review points are listed in the release handoff.
