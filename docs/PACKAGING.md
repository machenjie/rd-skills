# Packaging

Packaging uses built profile outputs from `dist/universal/skills/<profile>`.

```bash
python3 scripts/build.py --profile recommended
python3 scripts/package.py --profile recommended
```

`scripts/build.py` also refreshes `dist/openai-api/zips/<profile>` for the profile being built.

## Zip Contract

Each OpenAI API zip bundle is written to:

```text
dist/openai-api/zips/<profile>/<skill-name>.zip
```

Each zip must contain:

- Exactly one top-level skill folder.
- Exactly one `SKILL.md`, located at the root of that skill folder.
- Only generated runtime content from `dist/`, never raw `src/` or raw registry content.

## Guardrails

Packaging enforces:

- Maximum 500 files per zip.
- Maximum 5 MiB uncompressed content per zip.
- Maximum 2 MiB per file.
- No generated personal asset mappings.
- No `toolbox-mapping.md`.

Zip file timestamps are normalized for reproducible output.

## Profile Effects

- `recommended` packages the 19 professional skills.
- `full` packages the 19 professional skills plus 7 domain extensions.
- `dev` packages 19 professional skills, 116 foundation capabilities, and 7 domain extensions.

Top-level profile counts are 19 for `recommended`, 26 for `full`, and 142 for `dev`.

Each profile zip directory is refreshed independently on build or packaging. Legacy unprofiled zips directly under `dist/openai-api/zips` are not valid release artifacts.

Packaged professional skills include compiled `references/`, but those references are selectively loaded by router-selected capability and L1/L2/L3/L4/L5 policy. References are a precision mechanism, not a dumping ground. Language capabilities are professional engineering rules, not language tutorials or personal technical asset mappings.
