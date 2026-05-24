# ChangeForge Skill Mesh

ChangeForge Skill Mesh is a professional product-change engineering Skill system. It is designed for authoring, validating, building, packaging, installing, upgrading, and uninstalling ChangeForge skills across supported agent runtimes.

This repository is an authoring/build/install repository. Runtime skills are generated into `dist/` and installed from build outputs only. Source folders under `src/` are never installed directly.

ChangeForge is self-contained. It does not ingest, scan, index, summarize, map, package, or install any personal technical asset library. It does not create external asset mappings or assume user-specific knowledge sources are available at runtime.

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

## Runtime Profiles

- `recommended`: installs 19 professional skills as top-level runtime skills, with 102 foundation capabilities compiled into professional skill `references/`.
- `full`: installs 19 professional skills plus 7 eligible domain extensions as top-level runtime skills, with 102 foundation capabilities compiled into professional skill `references/`.
- `dev`: installs 19 professional skills plus 102 foundation capabilities plus 7 domain extensions as top-level runtime skills for authoring and validation work.

Recommended and full profiles must not install all foundation capabilities as top-level global skills. Foundation capabilities are compiled into professional skill references unless the `dev` profile is explicitly selected.

Runtime top-level counts are 19 for `recommended`, 26 for `full`, and 128 for `dev`.

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

Run the authoring contract validators:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/eval-routing.py
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```

These scripts enforce the professional skill, foundation capability, domain extension, registry, and runtime artifact contracts while remaining safe before any skills exist.

Run extended routing fixture comparison when updating or verifying captured
actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## License Semantics

The repository tooling license is defined in `pyproject.toml` for the authoring, validation, build, packaging, and installer code. Runtime Skill frontmatter declares the license for each generated Skill independently. This split is intentional: repository/tooling policy and per-Skill runtime content policy are separate contracts, and build/install tooling preserves the per-Skill frontmatter instead of inheriting repository metadata.
