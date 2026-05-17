# ChangeForge Skill Mesh

ChangeForge Skill Mesh is a professional product-change engineering Skill system. It is designed for authoring, validating, building, packaging, installing, upgrading, and uninstalling ChangeForge skills across supported agent runtimes.

This repository is an authoring/build/install repository. Runtime skills are generated into `dist/` and installed from build outputs only. Source folders under `src/` are never installed directly.

ChangeForge is self-contained. It does not ingest, scan, index, summarize, map, package, or install any personal technical asset library. It does not create toolbox mappings for personal notes, language notes, framework notes, database notes, system notes, security notes, or historical documents. It assumes no personal knowledge base is available at runtime.

## Layers

ChangeForge has three authoring layers:

1. Professional Skills: top-level professional product-change skills with `SKILL.md` at runtime.
2. Foundation Capabilities: reusable engineering rules, benchmark names, selection criteria, and risk gates compiled into concise skill references.
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

- `recommended`: installs professional skills with foundation capabilities compiled into concise `references/`.
- `full`: installs professional skills plus eligible domain extensions as top-level skills.
- `dev`: may expose foundation capabilities and domain extensions for authoring and validation work.

Recommended and full profiles must not install all foundation capabilities as top-level global skills. Foundation capabilities are compiled into professional skill references unless the `dev` profile is explicitly selected.

## Guardrails

- Do not install `src/` directly.
- Do not install `src/registry` as runtime content.
- Do not create `src/toolbox`.
- Do not create `registry/toolbox.yaml`.
- Do not create or install personal asset mappings.
- Do not create beginner tutorials in `SKILL.md`.
- Runtime skills must be built into `dist/`.
- Installed skill folders must contain `SKILL.md` at their root.
- Generated files must be deterministic and reproducible.

## Validation

Run the authoring contract validators:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-registry.py
python3 scripts/validate-installation.py
```

These scripts enforce the professional skill, foundation capability, registry, and runtime artifact contracts while remaining safe before any skills exist.
