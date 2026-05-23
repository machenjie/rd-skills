# Routing Evaluation Golden Cases

This directory contains golden-prompt cases used by
`scripts/eval-routing.py` to validate ChangeForge's routing rules
(`src/registry/routing-rules.yaml`) and `docs/ROUTING_EXAMPLES.md`.

The evaluation is offline and rule-based. It does not invoke any agent
or model. It validates that each case is internally consistent,
references real registry items, and matches the risk-driven required-gate
rules and L1 anti-over-routing rules declared by the routing rules.

## Running

```bash
python3 scripts/eval-routing.py
```

Exits non-zero on any failure with a per-case explanation.

## Case schema

```yaml
id: <kebab-case unique id, e.g. l3-api-field-add>
description: |
  Short human-readable summary.
prompt: |
  The raw change request as a user would phrase it.
expected:
  complexity: L1 | L2 | L3 | L4 | L5
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

## Adding a case

1. Choose the smallest realistic prompt that exercises the routing
   decision you care about.
2. Pick the minimum-sufficient `expected.*` set. Resist adding skills
   "just in case".
3. Add a `forbidden.*` set covering the over-routing mistakes you want
   to prevent.
4. Run `python3 scripts/eval-routing.py` and fix any reported issues.
