# Agent Instructions

Codex must treat this repository as a ChangeForge skill-authoring repository.

## Repository Purpose

This repository exists only to author, validate, build, package, install, upgrade, and uninstall ChangeForge skills and approved ChangeForge runtime support artifacts. It is not a runtime user-specific content corpus and must not become one.

## Non-Negotiable Boundaries

- Do not add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- Do not add toolbox mappings for user-specific technical archives.
- Do not create `src/toolbox`.
- Do not create `registry/toolbox.yaml`.
- Do not assume a user-specific content corpus is available at runtime.
- Do not install `src/` directly.
- Do not install `src/registry` as runtime content.
- Do not install `src/hook-runtime` directly; optional hook runtime artifacts must be built into `dist/` first.

## Change Discipline

Every change to the skill system must be validated before handoff. At minimum, run:

```bash
python3 scripts/validate-skills.py
python3 scripts/validate-capabilities.py
python3 scripts/validate-domain-extensions.py
python3 scripts/validate-registry.py
python3 scripts/validate-skill-body-links.py
python3 scripts/validate-skill-content-size.py
python3 scripts/audit-skill-content.py
python3 scripts/eval-routing.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-skill-professionalism.py --coverage-matrix
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professionalism-regression.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/validate-stage-routing-architecture.py
python3 scripts/validate-hooks.py
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-pressure-behavior.py
python3 -m unittest discover -s tests
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-runtime-reference-links.py
python3 scripts/validate-installation.py
```

`eval-skill-professionalism.py` writes both the main eval and key foundation coverage matrix;
`--coverage-matrix` writes only the coverage matrix reports for release checklist compatibility.

Run extended routing fixture comparison when updating or verifying captured actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Runtime Content Rules

Runtime skills must be emitted into `dist/`. Installed skill folders must contain `SKILL.md` at their root. Foundation capabilities are compiled into professional skill `references/` unless the development profile is selected. Optional project-level hook runtime artifacts are support artifacts, not skills, and must also be emitted into `dist/`.

`SKILL.md` is loaded when a skill is selected. `references/` is not assumed to be fully loaded automatically. The router selects capabilities, and professional skills read only selected capability references according to the L1/L2/L3/L4/L5 `Reference Loading Policy`.

References are a precision mechanism, not a dumping ground. Programming language knowledge is represented as professional engineering rules and language-runtime capabilities, not as personal technical asset mapping or beginner guides.

## Agent Execution Discipline

Every agent-assisted change must obey these execution rules:

1. No evidence, no completion.
2. No verified cause, no diagnosis.
3. No repeated same-path retry after two failures.
4. No local fix without same-pattern scan.
5. No new structure without reuse and placement rationale.
6. No handoff without risk, boundary, and validation result.

These rules are behavior constraints only. Do not add entertainment rhetoric, corporate-flavor narration, user-shaming language, or runtime-specific PUA state files. Optional hook runtime state, when present, must stay outside the project source tree and remain warning-only unless a maintainer explicitly enables stricter behavior.
