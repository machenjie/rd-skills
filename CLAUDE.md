# Claude Code Instructions

Claude Code should treat this repository as a ChangeForge Skill authoring project.

This repository is used only to author, validate, build, package, install, upgrade, and uninstall ChangeForge skills. Runtime output is built into `dist/` and installed from build artifacts.

Do not install `src/` directly. Do not install `src/registry` as runtime content.

Do not create personal knowledge mappings. Do not ingest, scan, index, summarize, map, package, or install personal technical asset libraries. Do not create toolbox mappings for personal notes, language notes, framework notes, database notes, system notes, security notes, or historical documents.

Do not create `src/toolbox` or `registry/toolbox.yaml`.

Validate every change to the skill system before handoff:

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

Run extended routing fixture comparison when updating or verifying captured actual router outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Agent Execution Discipline

Every agent-assisted change must obey these execution rules:

1. No evidence, no completion.
2. No verified cause, no diagnosis.
3. No repeated same-path retry after two failures.
4. No local fix without same-pattern scan.
5. No new structure without reuse and placement rationale.
6. No handoff without risk, boundary, and validation result.

These rules are behavior constraints only. Do not add entertainment rhetoric, corporate-flavor narration, user-shaming language, or runtime-specific PUA state files.
