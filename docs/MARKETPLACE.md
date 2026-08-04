# Marketplace Index

The marketplace index and catalog are local, source-derived discovery views. They are not a separate package format, duplicated registry, or user-specific toolbox. Official marketplace publishing is not implemented.

## Choose And Find Skills

1. Choose `recommended` for normal use, `full` when eligible Domain Skills must
   be top-level, or `dev` for authoring visibility. Confirm composition in
   [Build profiles](BUILD_PROFILES.md).
2. Open the generated [Marketplace Catalog](MARKETPLACE_CATALOG.md) and use its
   quick navigation to browse Control, Professional, Foundation, or Domain
   Skills.
3. Start with a Professional Skill when looking for a complete engineering
   judgment. Trigger and profile-delivery views help confirm discoverability;
   they do not instruct an agent to load the entire catalog.
4. Use the catalog name to locate the registry-owned entry and built artifact.
   The catalog is a discovery projection, not the source of routing or install
   truth.

Marketplace schema v3 is fail-closed. Every item carries explicit
`task_routable` metadata: a boolean for Professional Skills and `null` for all
other layers. Consumers must reject legacy v2 payloads rather than infer this
field from local source state.

## Layers

| Type | Profile exposure |
| --- | --- |
| Control Skill | top-level in recommended, full, and dev |
| Professional Skill | top-level in recommended, full, and dev |
| `product` Foundation Skill | targeted compiled reference in normal builds; top-level in dev |
| `authoring-only` / `dev-only` Foundation Skill | routing index only in normal builds; top-level in dev |
| Domain Skill | targeted compiled reference; top-level in full and dev |

## Source Fields

Every registry entry provides:

- `name` and source `path`;
- Foundation `delivery_scope` (`product`, `authoring-only`, or `dev-only`);
- Professional `task_routable` as an explicit boolean;
- `role_support`;
- `trigger_signals`, Domain `boundary_signals`, and `anti_trigger_signals`;
- `required_inputs`;
- `required_inputs_by_role` for every multi-role Professional Skill;
- `output_contract`;
- `output_contract_by_role` for every multi-role Professional Skill;
- `escalation_signals`;
- structured Reference Contract v2 entries (`path`, `type`, `load_when`,
  `do_not_load_when`, `required_by`, and `required_output`).

The exported marketplace index projects these contracts to their stable path
list for discovery compatibility; built root `SKILL.md` files render the link
plus load, skip, required-role, and required-output projection.

Professional entries may name Layer 3 candidates, but a task loads them only for a concrete signal.
Only `product` Foundation Skills may appear in those candidate lists, and their
`used_by` declarations exactly mirror the Professional owners.
For multi-role Professional entries, `output_contract` is the shared union and
`output_contract_by_role` preserves the exact Analysis, Task, or Review handoff.

## Export and Validate

```bash
python3 scripts/export-marketplace-index.py --profile recommended --out /tmp/recommended-marketplace-index.json
python3 scripts/generate-marketplace-catalog.py --profile recommended --out docs/MARKETPLACE_CATALOG.md
python3 scripts/validate-marketplace-index.py --profile recommended
```

The exporter must read the four source registries and match built artifacts. Do not hand-author a conflicting inventory or use a generated catalog to claim external availability.
