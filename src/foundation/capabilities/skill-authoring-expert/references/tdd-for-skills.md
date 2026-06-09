# TDD for Skills Reference

Deep support for `skill-authoring-expert`. The capability body carries the
decision rules; this file holds the behavior-test loop, templates, and failure
modes. Load it when authoring or auditing a skill change, not on every change.

## The Behavior-First Loop

A skill change is a behavior change, so prove the behavior, not just the prose.

1. **Baseline failure.** Show that an agent without the change fails the target
   behavior: skips the router, claims completion without evidence, over-routes a
   trivial change, reads only the description, or adds structure without reuse.
   Capture the baseline as a routing case, an agent-behavior sample, or a
   pressure case.
2. **Change the skill.** Make the smallest skill or reference edit that should
   move the behavior.
3. **Prove the change.** Re-run the same case and show the behavior now passes.
   The before and after are the evidence; the prose change alone is not.
4. **Name the rationalizations.** Write down the excuses an agent will use to
   skip the rule, and make the rule and its eval reject each one.

When a baseline is genuinely impossible (for example a brand-new capability with
no prior behavior), state why, and still provide the expected-behavior case the
change must pass.

## Baseline Failure Template

- **Target behavior**: the behavior the change should produce.
- **Baseline prompt or scenario**: the input that exposes the gap.
- **Expected failure without the change**: what a current agent does wrong.
- **Expected behavior after the change**: what the changed skill should make it
  do.
- **Evidence location**: the routing case, agent-behavior sample, or pressure
  case that captures both states.

## Test Type Selection

Match the skill change to the cheapest test that can fail for the right reason:

| Change | Test type | Where |
| --- | --- | --- |
| New or changed routing trigger | routing case (+ over-routing guard) | `evals/routing/` |
| New or changed discipline rule | pressure case | `evals/pressure/<area>/` |
| Reference split or loading policy | reference retrieval check | reference link validation + dev build |
| New or changed output contract | output contract assertion | agent-behavior sample |
| Hook reminder behavior | hook fixture | `tests/hook_runtime/`, `tests/fixtures/hooks/` |
| End-to-end routing manifest | agent-behavior sample | `evals/agent-behavior/samples/` |

## Failure Modes

- Editing a rule with no baseline failure, so there is no proof the rule changes
  behavior.
- Adding a routing trigger with no over-routing guard, so the trigger silently
  widens routing.
- Writing a new rule that the agent can bypass with an unaddressed
  rationalization.
- Moving content to a reference without a loading policy, so it is never loaded.
- Letting the body grow instead of moving deep content to a reference.
