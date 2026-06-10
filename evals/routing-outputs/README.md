# Routing Output Fixtures

This directory contains captured router-output YAML used by
`scripts/eval-routing.py --candidate-output-dir evals/routing-outputs`.

Each file maps to one golden case in `evals/routing/` by `case_id` and
uses the normalized actual-output schema:

```yaml
case_id: <golden case id>
actual:
  complexity: L1 | L2 | L3 | L4 | L5
  risk_level: low | medium | high | critical
  skills: [...]
  capabilities: [...]
  domain_extensions: [...]
  quality_gates: [...]
  required_references:
    - references/routing-rules.md
    - references/capabilities/<id>-<capability>.md
  stage_route_manifest:
    schema_version: 1
    current_stage: <expected engineering stage for L2-L5 cases>
    next_stage: <allowed next stage or closed>
    product_surface: <stage-model product surface or none>
    language_surface: <stage-model language surface or none>
    selected_skills: [...]
    selected_capabilities: [...]
    selected_domain_extensions: [...]
    skipped_capabilities:
      - capability: <skipped capability>
        reason: <why it is skipped this stage>
    context_budget_mode: minimal | single-stage | staged-plan
    context_budget_rationale: <why this budget fits the change level>
    required_evidence: [...]
    required_quality_gates: [...]
    handoff_target: <stage, selected owner, blocked, or closed>
```

The comparison mode also accepts `{skill, reference}` mappings when PyYAML
is available, but repository fixtures use plain reference-path strings so the
built-in YAML fallback parser can read them. Captured outputs must include
router reference paths, selected capability reference paths, and a complete
stage route manifest for L2-L5 cases. Stage names, transitions, product
surfaces, language surfaces, evidence, and default-forbidden capabilities are
validated against `src/registry/stage-model.yaml`.
