# Skill Efficacy Benchmarks

This directory contains offline benchmark definitions for evaluating whether a
foundation capability improves agent workflow behavior on ChangeForge authoring
tasks. These fixtures are structural regression guards: they validate that a
capability is selected for the right failure mode and that the treatment records
the expected evidence shape.

The definitions do not call a model and do not claim measured improvement unless
the fixture supplies numeric cost and outcome data. `not_collected` is the
required value when token or turn overhead has not been measured.

## Layout

Each benchmark is a single YAML file:

```text
evals/skill-efficacy/
  repository-context-map-placement.yaml
  plan-execution-consistency-drift.yaml
  agent-tool-permission-sandbox-command.yaml
```

## Running

```bash
python3 scripts/validate-skill-efficacy-benchmarks.py
```

The validator checks that every benchmark references a real capability, that the
treatment selects that capability, that baseline and treatment cost fields are
present, that overhead metrics are explicit, and that no fixture claims measured
efficacy from `not_collected` data.

