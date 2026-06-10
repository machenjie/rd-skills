# Route Manifest Schemas

Deep reference for the `### Machine-Readable Route Manifests` summary in the ChangeForge
Router `Output Contract`. The router body carries the compact field list and projection
rules; this file carries the full YAML schemas, field templates, and manifest rules. Hooks,
`doctor`, telemetry review, and the routing/agent-behavior eval tools parse the emitted
manifests from agent output; this reference documents their shape. The manifests never
replace the human-readable routing result and never authorize any tool to mutate skills,
routing rules, or capabilities.

## changeforge_route

After the Markdown Routing Result, emit one fenced YAML block named `changeforge_route`. The
Markdown result stays the human-readable explanation; the manifest is the machine-readable
summary that hooks, doctor, telemetry review, and routing/agent-behavior eval tools parse.

```yaml
changeforge_route:
  schema_version: 1
  route_id: <kebab-case id for this routing decision>
  complexity: <L1|L2|L3|L4|L5>
  risk_level: <low|medium|high|critical>
  execution_mode: <clarify|analyze|plan|implement|review|release|document|blocked>
  selected_skills:
    - <professional skill name>
  selected_capabilities:
    - <capability name (must map to a selected skill via used_by)>
  selected_domain_extensions:
    - <domain extension name, or omit when none>
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
    - <references/capabilities/<id>-<name>.md for each selected capability>
  required_quality_gates:
    - <gate name that must close before release>
  skipped_quality_gates:
    - gate: <gate name>
      reason: <why this gate is not needed>
  blocking_questions:
    - <question that blocks safe execution, or omit when none>
  assumptions:
    - <explicit assumption used in place of a missing answer>
  handoff_target: <next skill name or blocked>
```

Manifest rules:

- `selected_capabilities` must each map to a `selected_skills` entry through the capability `used_by` relationship, unless the capability is explicitly marked as a route-level capability in the registry. Do not list an ordinary capability whose owning skill is absent.
- `required_references` must include the four router self-use references above plus the deterministic `references/capabilities/<capability-id>-<capability-name>.md` path for every selected capability.
- `skipped_quality_gates` must give a `reason` for each skipped gate; never drop a gate silently. A gate is either in `required_quality_gates` or in `skipped_quality_gates` with a reason.
- Keep `selected_skills`, `selected_capabilities`, `required_quality_gates`, and `skipped_quality_gates` consistent with the Markdown sections; the manifest is a projection of the same decision, not a second route.
- The manifest is read by tooling. It does not substitute for the human-readable routing explanation, and it does not authorize any tool to mutate skills, routing rules, or capabilities.

## changeforge_stage_route

For non-trivial engineering tasks, also emit one fenced YAML block named
`changeforge_stage_route`. It is the machine-readable projection of the `## Stage
Professionalism` section and of the `engineering-stage-professionalism` Stage Professional
Launch Plan. It records the current and next engineering stage, the product and language
surface, the capabilities launched this stage, the heavy capabilities explicitly skipped with
a reason, the context budget, required evidence, required gates, and the next-stage handoff.
It does not replace the human-readable routing result and does not authorize any tool to
mutate skills.

```yaml
changeforge_stage_route:
  schema_version: 1
  current_stage: <requirement-intake|architecture-design|implementation-planning|coding|debugging-diagnosis|bug-fix|code-review|refactoring|testing|release-delivery|documentation-handoff|skill-authoring>
  next_stage: <next engineering stage or closed>
  product_surface: <product surface, or none>
  language_surface: <language, or none>
  selected_skills: []
  selected_capabilities: []
  selected_domain_extensions: []
  skipped_capabilities:
    - capability: <heavy capability not launched this stage>
      reason: <why it is skipped this stage>
  context_budget_mode: <minimal|single-stage|staged-plan>
  context_budget_rationale: <why this budget fits the change level>
  required_evidence: []
  required_quality_gates: []
  handoff_target: <next stage owner skill or blocked>
```

Stage manifest rules:

- Emit `changeforge_stage_route` only for non-trivial engineering tasks; omit it for a single trivial edit whose stage is obvious.
- `current_stage` must be one engineering stage; a cross-stage task is split and re-emitted per stage rather than collapsed into one plan.
- Every entry in `skipped_capabilities` must carry a `reason`; a heavy capability is either launched this stage or skipped with a reason, never dropped silently.
- `context_budget_mode` is `minimal` for L1, `single-stage` for L2, and `staged-plan` for L3 and higher.
- The stage manifest is consistent with `changeforge_route`; it sequences professional launch within the same route, it does not define a second route.
