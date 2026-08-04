# Routing Maintenance Checklist

Use only while authoring or auditing rd-skills routing assets.

- Confirm each task route has one primary Professional Skill and one Review
  Skill.
- Confirm Layer 3 candidates have a concrete trigger and anti-trigger.
- Reject routes to compatibility-only Skills.
- Keep the installed router reference short and deterministic.
- Run `python3 scripts/validate-skill-routing.py` and the routing evaluation.

Ordinary engineering tasks are routed once by `engineering-control-plane`; do
not invoke this compatibility Skill inside a dispatched task.
