# Agent Instructions

Codex must treat this repository as a ChangeForge skill-authoring repository.

## Repository Purpose

This repository exists only to author, validate, build, package, install, upgrade, and uninstall ChangeForge skills. It is not a runtime user-specific content corpus and must not become one.

## Non-Negotiable Boundaries

- Do not add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- Do not add toolbox mappings for user-specific technical archives.
- Do not create `src/toolbox`.
- Do not create `registry/toolbox.yaml`.
- Do not assume a user-specific content corpus is available at runtime.
- Do not install `src/` directly.
- Do not install `src/registry` as runtime content.

## Change Discipline

Every change to the skill system must be validated before handoff. At minimum, run:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/eval-routing.py
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```

## Runtime Content Rules

Runtime skills must be emitted into `dist/`. Installed skill folders must contain `SKILL.md` at their root. Foundation capabilities are compiled into professional skill `references/` unless the development profile is selected.

`SKILL.md` is loaded when a skill is selected. `references/` is not assumed to be fully loaded automatically. The router selects capabilities, and professional skills read only selected capability references according to the L1/L2/L3/L4/L5 `Reference Loading Policy`.

References are a precision mechanism, not a dumping ground. Programming language knowledge is represented as professional engineering rules and language-runtime capabilities, not as personal technical asset mapping or beginner guides.
