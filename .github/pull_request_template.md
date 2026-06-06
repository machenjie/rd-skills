## Summary

- 

## Scope

- Affected skills, capabilities, registries, docs, installers, scripts, or evals:
- Runtime profiles affected: `recommended` / `full` / `dev` / none
- Agent targets affected: `codex` / `claude` / `copilot` / `openai-api` / none

## Validation

Paste the commands run and the result:

```text

```

Required for skill-system changes:

- [ ] `python3 scripts/validate-skills.py`
- [ ] `python3 scripts/validate-capabilities.py`
- [ ] `python3 scripts/validate-domain-extensions.py`
- [ ] `python3 scripts/validate-registry.py`
- [ ] `python3 scripts/validate-skill-body-links.py`
- [ ] `python3 scripts/validate-skill-content-size.py`
- [ ] `python3 scripts/eval-routing.py`
- [ ] `python3 scripts/validate-hooks.py`
- [ ] `python3 -m unittest discover -s tests`
- [ ] `python3 scripts/validate-codegen-benchmarks.py`
- [ ] `python3 scripts/run-codegen-benchmarks.py --limit 3`
- [ ] `python3 scripts/build.py --profile recommended`
- [ ] `python3 scripts/build.py --profile full`
- [ ] `python3 scripts/build.py --profile dev`
- [ ] `python3 scripts/validate-runtime-reference-links.py`
- [ ] `python3 scripts/validate-installation.py`

## Boundary Check

- [ ] Does not install `src/` directly.
- [ ] Does not install raw `src/registry` content.
- [ ] Does not add personal asset ingestion, scanning, indexing, summarization, mapping, packaging, or installation.
- [ ] Does not add `src/toolbox`, `registry/toolbox.yaml`, or toolbox mappings.
- [ ] Keeps generated runtime skills rooted in `dist/` outputs.

## Risk And Release Notes

- Compatibility impact:
- Rollback path:
- Documentation updated:
- Unresolved assumptions or maintainer decisions:
