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
python3 scripts/eval-routing.py
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/validate-installation.py
```
