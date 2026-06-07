# Routing Evaluation Golden Cases

This directory contains golden-prompt cases used by
`scripts/eval-routing.py` to validate ChangeForge's routing rules
(`src/registry/routing-rules.yaml`) and `docs/ROUTING_EXAMPLES.md`.

The default evaluation is offline and rule-based. It does not invoke any
agent or model. It validates that each case is internally consistent,
references real registry items, and matches the risk-driven required-gate
rules and L1 anti-over-routing rules declared by the routing rules.

The same script can also compare captured router output YAML from
`evals/routing-outputs/` against these golden cases. That mode still does
not call a model; it checks an already-produced router result.

## Running

```bash
python3 scripts/eval-routing.py
```

Exits non-zero on any failure with a per-case explanation.

Compare one captured output:

```bash
python3 scripts/eval-routing.py \
  --candidate-output evals/routing-outputs/backend-auth-idor.actual.yaml
```

Compare the fixture directory and require at least 10 actual outputs:

```bash
python3 scripts/eval-routing.py --candidate-output-dir evals/routing-outputs
```

## Case schema

```yaml
id: <kebab-case unique id, e.g. l3-api-field-add>
description: |
  Short human-readable summary.
prompt: |
  The raw change request as a user would phrase it.
expected:
  complexity: L1 | L2 | L3 | L4 | L5
  risk_level: low | medium | high | critical
  structure_required: false  # optional override for pure config/test/text/L1 exceptions
  expected_stage: requirement-intake | architecture-design | implementation-planning | coding | debugging-diagnosis | bug-fix | code-review | refactoring | testing | release-delivery | documentation-handoff | skill-authoring
  expected_context_budget_mode: minimal | single-stage | staged-plan
  expected_required_references:
    - references/capabilities/<id>-<capability-name>.md
  stage_route_required: false  # optional; must include stage_route_skip_reason
  stage_route_skip_reason: <why no stage route applies>
  risk_triggers:
    - <one or more values from routing-rules.yaml:risk_escalation_triggers>
  skills:
    - <professional skill names from src/registry/skills.yaml>
  capabilities:
    - <foundation capability names from src/registry/capabilities.yaml>
  domain_extensions:
    - <domain extension names from src/registry/domain-extensions.yaml>
  quality_gates:
    - <gate names from routing-rules.yaml:quality_gates>
forbidden:
  skills: [...]
  capabilities: [...]
  domain_extensions: [...]
  quality_gates: [...]
notes: |
  Rationale and any anti-over-routing intent worth recording.
```

`forbidden.*` blocks are the negative side of the contract. They prove
that the router does not over-attach gates or extensions when the change
does not warrant them.

## What the script enforces

- Schema and types; `id` unique and kebab-case; complexity in L1..L5.
- `expected.risk_level`, when present, is one of `low`, `medium`,
  `high`, or `critical`; it is required for router-output comparison.
- `expected.structure_required`, when present, is a boolean. It can be
  set to `false` only when an implementation-gate case is a pure
  configuration, pure test, pure text, or L1-small change that does not
  need a structure plan.
- `expected.expected_stage` must be present for L2-L5 cases unless
  `expected.stage_route_required: false` is set with a skip reason. It
  declares the expected canonical `changeforge_stage_route.current_stage`
  in captured router output.
- `expected.expected_context_budget_mode`, when present, must be one of
  `minimal`, `single-stage`, or `staged-plan`. Captured output defaults
  are `minimal` for L1, `single-stage` for L2, and `staged-plan` for
  L3-L5.
- `expected.expected_required_references`, when present, lists additional
  runtime reference paths that captured output must include.
- `expected.stage_route_required: false` can suppress the L2-L5 stage
  route requirement only when `expected.stage_route_skip_reason` explains
  why the case has no applicable stage route.
- All `expected.*` and `forbidden.*` names exist in their respective
  registries.
- `risk_triggers` are drawn from `routing-rules.yaml:risk_escalation_triggers`.
- `quality_gates` are drawn from `routing-rules.yaml:quality_gates`.
- `expected.*` and `forbidden.*` are disjoint per field, with no
  duplicates inside a field.
- Risk-driven required-gate rules derived from the routing rules. For
  example:
  - `auth`, `authorization`, `object-level permission`, `user data`,
    `PII`, `webhook`, `secret/config change`, `AI prompt`, `RAG`,
    `payment`, `subscription`, `billing`, `wallet`, `private key`,
    `Web3 asset` → `security-privacy-gate` must be in `expected.skills`.
  - `database migration`, `irreversible data operation` →
    `data-api-contract-changer` and `delivery-release-gate` must be in
    `expected.skills`.
  - `production deployment` → `delivery-release-gate` must be in
    `expected.skills`.
  - `production incident` → `reliability-observability-gate` and
    `change-documentation-gate` must be in `expected.skills`.
  - `cloud IAM`, `public exposure` → `security-privacy-gate` must be in
    `expected.skills`.
  - `regulated workload`, `compliance evidence` →
    `security-privacy-gate`, `delivery-release-gate`, and
    `change-documentation-gate` must be in `expected.skills`.
  - `cost anomaly` → `reliability-observability-gate` must be in
    `expected.skills`.
  - `webhook`, `external integration` → `integration-change-builder`
    must be in `expected.skills`.
  - `payment`/`subscription`/`billing` → `payment-trading-extension` in
    `expected.domain_extensions`.
  - `wallet`/`private key`/`Web3 asset` → `web3-product-extension` in
    `expected.domain_extensions`.
  - `AI prompt`/`RAG` → `ai-product-extension` in
    `expected.domain_extensions`.
- L1 anti-over-routing: design-time, security, reliability, release,
  data/middleware, integration, and architecture skills must not appear
  in `expected.skills` for L1 cases, and `expected.domain_extensions`
  must be empty.
- For L2..L5 cases, `expected.quality_gates` must contain at least one
  of `implementation gate`, `test gate`, or `documentation gate` so the
  case carries verifiable evidence.
- For L2..L5 cases, `backend-change-builder`, `frontend-change-builder`,
  or `ai-code-review-refactor` combined with `implementation gate`
  requires `implementation-structure-design` in `expected.capabilities`,
  unless `expected.structure_required: false` is explicitly set.
- The corpus contains at least 30 golden cases.
- The corpus contains at least 8 L1 anti-over-routing cases.
- Every domain extension appears in at least 2 golden cases.

## Router Output Comparison

Captured actual outputs live under `evals/routing-outputs/` and use this
normalized schema:

```yaml
case_id: backend-auth-idor
actual:
  complexity: L3
  risk_level: high
  skills:
    - backend-change-builder
  capabilities:
    - permission-boundary-modeling
  domain_extensions: []
  quality_gates:
    - security gate
  required_references:
    - references/routing-rules.md
    - references/skill-registry.md
    - references/capability-index.md
    - references/domain-extension-index.md
    - references/capabilities/16-permission-boundary-modeling.md
  stage_route_manifest:
    current_stage: bug-fix
    context_budget_mode: staged-plan
    skipped_capabilities:
      - capability: release-rollback
        reason: no release sequencing required for this route
```

`required_references` may use plain runtime paths or legacy
`skill:reference-path` entries. Selected foundation capabilities must include
their deterministic compiled path:
`references/capabilities/<id>-<capability-name>.md`.

The comparison mode enforces:

- `expected.skills` and `expected.capabilities` all appear in actual output.
- `forbidden.skills` and `forbidden.capabilities` do not appear.
- `expected.domain_extensions` and `expected.quality_gates` all appear.
- `forbidden.domain_extensions` and `forbidden.quality_gates` do not appear.
- Complexity and risk level match the golden case.
- Router self-use references are present in `actual.required_references`.
- L2-L5 actual output includes `changeforge_stage_route` or
  `stage_route_manifest`, unless the golden case explicitly disables that
  requirement with a skip reason.
- `current_stage` is a canonical stage from
  `routing-rules.yaml:engineering_stage_signals`, and `current_stage` and
  `context_budget_mode` match the golden case or the complexity-derived
  default.
- Every selected capability exists in the registry, belongs to at least one
  selected skill or domain extension through `used_by`, and has its
  deterministic compiled capability reference in `actual.required_references`.
- Any skipped capability in the stage route includes a concrete reason.
- L1 actual output does not over-route to heavyweight skills or domain
  extensions unless the golden case declares a matching risk trigger.
- L4/L5 actual output does not omit any expected security, reliability,
  delivery, or documentation gate/skill pair.

## Adding a case

1. Choose the smallest realistic prompt that exercises the routing
   decision you care about.
2. Pick the minimum-sufficient `expected.*` set. Resist adding skills
   "just in case".
3. Add a `forbidden.*` set covering the over-routing mistakes you want
   to prevent.
4. Run `python3 scripts/eval-routing.py` and fix any reported issues.
