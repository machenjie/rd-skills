# Hookless Agent Behavior Evals

This directory contains checked-in, human-reviewed handoff fixtures. The
evaluators do not call a model, inspect private reasoning, or represent captures
as host-execution evidence.

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

Run:

```bash
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
```

Generated reports are written to `evals/agent-behavior/outputs/` and
`reports/professional-agent-samples-report.*`. Captured-fixture scores prove only
deterministic fixture conformance, not host performance, production accuracy,
or adoption.
