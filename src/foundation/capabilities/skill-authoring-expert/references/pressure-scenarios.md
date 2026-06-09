# Pressure Scenarios Reference

Deep support for `skill-authoring-expert`. Discipline-enforcing skills must hold
up under pressure, not only on a cooperative path. This file catalogs the
pressure scenarios a skill change must defend against and the rationalizations
each one must reject. Load it when authoring or auditing a discipline rule or a
routing trigger, not on every change.

## What A Pressure Scenario Is

A pressure scenario pairs a realistic excuse to skip the rule with the behavior
the rule must still enforce. A rule that only works when the agent cooperates is
not enforced. Each scenario names the rationalization to reject, so the rule and
its eval can close it.

## Required Coverage

A skill change that adds or strengthens a discipline rule or a routing trigger
must defend at least the relevant scenarios below.

1. **Edit without baseline.** Pressure: "the change is obviously right, it needs
   no test." Required: a baseline failure scenario, or a stated reason the
   baseline is impossible plus an expected-behavior case.
2. **New trigger without over-routing guard.** Pressure: "add the trigger so we
   never miss it." Required: a guard case proving a trivial L1 change does not
   pull in the new trigger.
3. **Strong rule bypassed as a small change.** Pressure: "it is just a tiny
   change, the discipline does not apply." Required: the rule fires regardless of
   change size, and a pressure case proves it.
4. **Reference bloat into the body.** Pressure: "keep it in the body so it is
   always visible." Required: deep content moves to a reference with a loading
   policy; the body stays within the context budget.
5. **Description as a workflow shortcut.** Pressure: "summarize the whole process
   in the description so the agent can act from it." Required: the description
   states only when to use the skill; the workflow stays in the body, and a check
   flags a workflow-summary description.

## Pressure Case Fields

A pressure case records both the excuse and the required behavior:

- **id**: stable identifier.
- **pressure_type**: which scenario above it exercises.
- **prompt**: the realistic request that applies the pressure.
- **expected_route** / **required_capabilities**: the path the change must hold.
- **required_evidence**: the evidence the closure must carry.
- **forbidden_behaviors**: what the agent must not do under pressure.
- **rationalizations_to_reject**: the exact excuses the rule must close.
- **completion_claim_allowed**: whether a completion claim is permitted here.
- **expected_handoff_fields**: the closure fields the handoff must contain.

## Failure Modes

- A rule that holds on the cooperative path but collapses under a plausible
  excuse.
- A pressure case that asserts the happy path and never applies real pressure.
- A rationalization the rule never names, so the agent uses it freely.
- A routing trigger that widens routing with no guard against over-routing.
