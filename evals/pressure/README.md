# Hookless Pressure Scenarios

The formal suite under `hookless/` records bounded, human-reviewed captures for
pressure that can make an AI agent violate the Hookless control contract. The
evaluator never calls a model or treats these fixtures as host-execution
evidence.

```bash
python3 scripts/eval-pressure-behavior.py
```

Each case declares:

- a concrete prompt and pressure type;
- one expected Profile and primary Professional Skill;
- zero to three Layer 3 Skills that must be candidates of that primary Skill;
- one Review Skill that supports `review-agent`;
- required observable behavior and forbidden shortcuts;
- a captured route, validation status, residual risk, and completion claim;
- `evidence_kind: captured-fixture`.

The evaluator checks route-once selection, Profile compatibility, Layer 3 JIT
loading, pressure resistance, forbidden-behavior absence, and honest validation
claims. Scores establish fixture conformance only. They do not establish host
performance, production accuracy, or adoption readiness.
