# Marketplace Index

The marketplace index is a machine-readable discovery export. The marketplace catalog is a generated human-readable discovery view over the same source data. These are local discovery assets only: official Codex and Claude marketplace publishing is intentionally not implemented.

The index and catalog are not a new runtime package format, not a duplicated registry, not an official marketplace listing, and not a user-specific toolbox. Do not use these files to claim Codex/Claude marketplace availability.

## Asset Types

| Type | Meaning | Profile Exposure |
| --- | --- | --- |
| `professional_skill` | Top-level skill that owns a product/code change action. | Top-level in `recommended`, `full`, and `dev`. |
| `foundation_capability` | Reusable engineering rule/reference selected by a professional route. | Compiled reference in `recommended` and `full`; top-level only in `dev`. |
| `domain_extension` | Optional domain-specific professional extension. | Router index in `recommended`; top-level in `full` and `dev`. |

## Export

```bash
python3 scripts/export-marketplace-index.py --profile recommended --out dist/indexes/recommended-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile full --out dist/indexes/full-marketplace-index.json
python3 scripts/export-marketplace-index.py --profile dev --out dist/indexes/dev-marketplace-index.json
```

`dist/` is ignored as generated output. For local review or CI smoke checks, write to `/tmp`:

```bash
python3 scripts/export-marketplace-index.py --profile recommended --out /tmp/recommended-marketplace-index.json
```

Validate the generated contract after the corresponding runtime profile has been built:

```bash
python3 scripts/validate-marketplace-index.py --profile recommended
python3 scripts/validate-marketplace-index.py --profile full
python3 scripts/validate-marketplace-index.py --profile dev
```

## Catalog

Generate the combined human-readable catalog:

```bash
python3 scripts/generate-marketplace-catalog.py --profile recommended --out docs/MARKETPLACE_CATALOG.md
```

Validate the committed catalog snapshot:

```bash
python3 scripts/generate-marketplace-catalog.py --profile recommended --check --out docs/MARKETPLACE_CATALOG.md
```

`docs/MARKETPLACE_CATALOG.md` is generated from the same exporter-backed source as the machine index. Do not hand-author a separate catalog.

## Fields

The schema lives at [../schemas/marketplace-index.schema.json](../schemas/marketplace-index.schema.json). Each item includes:

- `name`
- `type`
- `profile_visibility`
- `summary`
- `triggers`
- `risk_notes`
- `expected_outputs`
- `used_by`
- `required_quality_gates`
- `runtime_path`
- `source_path`

## Discovery Rules

Use the index to filter by:

- change type or risk trigger through `triggers`
- domain through `type=domain_extension`
- quality gate through `required_quality_gates`
- reuse owner through `used_by`
- runtime exposure through `profile_visibility.top_level`

The exporter reads source registries and frontmatter. Do not hand-author a second marketplace catalog.
The validator checks schema shape, profile visibility, runtime paths, and foundation capability exposure rules against built `dist/` artifacts.
Business semantic capability discovery comes from the same source-derived index and generated catalog as every other capability; do not hand-author a separate business catalog or runtime content package.
The canonical business semantic triggers are business context missing, business
vocabulary ambiguous, business object ownership unclear, business rule authority
unknown, business workflow state unclear, business invariant changed, business
rule hidden in SQL/controller/UI/test, DTO used as business object, business
memory affects decision, business golden case missing, technical refactor may
change business semantics, business semantic review required, graph used as
business fact, and memory used as business fact. Marketplace discovery should
surface those names while retaining legacy aliases for compatibility; BSP
references require structured rationale and memory/graph remain selectors until
confirmed by current source or validation. Business semantic fixture evidence is
deterministic and local: generated actual outputs must pass
`validate-business-semantic-generator.py` and
`generate-business-semantic-actuals.py --check`. Actual generation reads input
signals, bounded `input_route_hint`, resolver/routing rules, and source/diff
context, not `expected_*` oracle fields. Routing evals compare skills,
capabilities, gates, BSP scope, sections, triggers, references, forbidden
selections, and max selection limits; review evals check `expected_evidence`
against actual evidence derived from source/diff snippets, prompt, and routing
triggers; rule `reason_codes` / `entry_points` must be non-empty. This proves
deterministic local structure, not live agent behavior, live LLM behavior, or
live business correctness.
