# Hookless Agent Behavior Evals

This directory contains checked-in handoff fixtures and a dev/eval-only blind
OLD/NEW comparison harness. The evaluator never calls a model or inspects
private reasoning. It scores supplied observations only; a checked-in
structural comparison is not host-execution evidence.

The default suite is `professional-samples/`. Each YAML case declares one
expected dispatched Profile, one primary Professional Skill, zero to three
Layer 3 Skills, one Review Skill, professional obligations, forbidden
shortcuts, and a natural-language handoff.

The handoff contract is:

```text
Result
Changed Files
Commands Run
Validation Results
Findings
Unverified Scope
Residual Risk
Recommended Next Step
```

Validation checks that:

- the actual route matches the expected route once;
- the primary Skill supports the dispatched Profile;
- each Layer 3 Skill exists, is unique, is declared by the primary Skill, and
  the task loads at most three;
- the Review Skill supports `review-agent`;
- the handoff covers every required observable field and professional
  obligation;
- unverified validation has explicit limits and residual risk;
- no forbidden shortcut appears.

The comparison contract is owned only by
`src/control-model/core-contracts.json#/behavior_eval_contract`. The manifest
under `comparison-fixtures/` points to five physically separate artifacts:

- the agent-visible packet contains the task and controlled run bindings;
- the evaluator-only oracle contains expected routing and Review behavior;
- observations bind both opaque arms to the same task, Host, Model, Profile,
  repository state, evidence boundary, evaluator, and expected definition;
- caller-supplied captures bind the exact captured bytes and SHA-256, ordered
  baseline/candidate source identities, provenance, and the same controlled
  bindings. This proves capture integrity only: the repository has no
  Host/verifier-owned receipt channel, so effective live evidence remains
  `not_collected` and cannot promote a behavior verdict;
- the post-capture reveal maps the opaque arms to OLD and NEW only after both
  observations exist.

The evaluator rejects binding drift, non-opaque arm labels, early reveal, and
expected route or finding leakage into the agent packet. Routing metrics cover
path, start Profile, primary Professional Skill, Layer 3 precision/recall/F1,
Domain false positives/negatives, unnecessary Layer 3, safe fallback,
paraphrase stability, and boundary transitions. Review metrics cover primary
Review Skill, Review Layer 3 precision/recall/F1, required-specialist
recall/FNR/exact-set accuracy, unnecessary specialists, and
the fixed Review Boundary contract. The latter includes Review Input Ready,
the Main-owned pre-dispatch actor/candidate decision, Reviewer independence,
complete Initial Review, fresh repair evidence, focused
Re-review, duplicate-final-review avoidance, and exact structured finding
relations, materiality, eligibility, disposition, scope, and freshness. A
per-case NEW regression dominates suite averages, and partial NEW success is
not reported as improvement.

Verdicts and metric directions are also Core-derived. Structural fixtures
always report `structural_only`, `not_collected`, and
`not_enough_evidence`; they may prove harness plumbing and represented negative
controls, never live efficacy or elapsed-time improvement. A quality regression
remains a regression regardless of lower token, turn, or elapsed cost.

Run:

```bash
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-agent-behavior.py \
  --comparison-spec evals/agent-behavior/comparison-fixtures/structural.yaml
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
```

Generated reports are written to `evals/agent-behavior/outputs/` and
`reports/professional-agent-samples-report.*`. Captured and structural fixture
scores prove only deterministic fixture conformance, not host performance,
production accuracy, adoption, or latency.
