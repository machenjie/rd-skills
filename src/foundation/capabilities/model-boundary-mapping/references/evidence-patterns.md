# Model Boundary Mapping Evidence Patterns

Use this reference when model-boundary closure depends on validation freshness, prior source or task evidence claims, privacy or internal-field boundaries, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second schema-design guide.

## Boundary-Claim-To-Validation Map

| Boundary claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Model ownership is distinct | Source/target models, owners, layers, validation owner, mapping owner, contract surface, and rejected direct reuse | Inspected models have named responsibilities | Every downstream consumer understands the boundary |
| Leakage is prevented | Allowed/rejected field list, internal/sensitive field scan, mapper placement, and denied exposure test or review | Obvious internal or persistence fields were filtered | Unknown exports, dashboards, or logs cannot expose them |
| Mapper keeps translation separate from policy | Mapper code, policy owner, side-effect scan, business rule handoff, and tests | In the inspected mapping path, mapper responsibility is limited to semantic translation; policy and side effects stay with their named owners unless an additional adapter responsibility is explicitly assigned. | All sibling mappers follow the same pattern |
| Null/default semantics are preserved | Semantic table, old/new examples, negative cases, compatibility cases, and validator result | Material value meanings survive the mapped boundary | Every client language or generated SDK preserves semantics |
| Generated boundary is current | Source schema, generated artifact path, generator command or freshness, hand-edit rejection, and contract check | Generated code is treated as generated boundary | Future generator output or uninspected languages are safe |
| Public contract impact is governed | API/event/SDK/export exposure, known/unknown consumers, version/bridge need, contract tests, and owner | Public boundary risk was considered for inspected consumers | All external consumers are discovered |
| Validation is fresh after final mapping edit | Command/review/report path, changed boundary, exit code or manual result, final edit scope, and freshness | Evidence covers the final inspected mapping path | Production telemetry, rollback, or all consumer environments are proven |
| Tool output is safe to retain | Action class, permission state, redaction rule, artifact path, retention owner, and rollback or cleanup path | Evidence collection avoids obvious sensitive output leakage | Every future graph export or connector output is safe |

## Current Evidence And Freshness

- Treat repository inspection, generated artifacts, prior task evidence, prior incidents, fixtures, dashboards, reports, and validation output as selectors until current source, schemas, tests, contracts, and owner evidence confirm them.
- Accept prior "no boundary leak", "mapper tested", "no consumers", "generated client fresh", or "null semantics safe" only when current callers, consumers, generated outputs, fixtures, and validation still match.
- Mark boundary evidence stale after edits to source or target fields, mapper placement, validation owner, generated artifacts, serializers, events, public exports, fixtures, tests, reports, or build outputs.
- Map final model-boundary claims to fresh evidence or an explicit not-run disclosure.
- Name unknown consumers separately.

- If regenerating clients, schema export, contract fixture update, compatibility report, record generator/source, diff scope, rollback, and owner.
- If production data export, support query, live schema registry mutation, connector write, require owner approval, data class, rollback or containment path, and redaction rule.
