# Marketplace Index

The marketplace index is a machine-readable discovery export. It is not a new runtime package format, not a duplicated registry, and not a user-specific toolbox.

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
