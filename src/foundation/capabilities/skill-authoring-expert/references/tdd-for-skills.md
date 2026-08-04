# TDD for Skills Reference

Deep support for `skill-authoring-expert`. Load this file only when a Skill
routing, behavior, build, or installation contract changes and current evidence
does not expose the relevant regression. Skip prose-only changes and behavior
already covered by current deterministic evidence.

## The Behavior-First Loop

Start this loop when a claimed behavior change lacks deterministic coverage;
reuse current evidence when it already catches the regression.

1. **Expose the behavior gap.** Reuse a current failing case or negative control
   when it already proves the gap; otherwise add the smallest case that fails
   for the intended reason.
2. **Change the skill.** Make the smallest skill or reference edit that should
   move the behavior.
3. **Prove the change.** Re-run the same case and show the behavior now passes.
   The before and after are the evidence; the prose change alone is not.
4. **Name the rationalizations.** Write down the excuses an agent will use to
   skip the rule, and make the rule and its eval reject each one.

For a brand-new capability with no prior behavior, add the expected-behavior
case plus a negative control for its anti-trigger or failure boundary. Do not
manufacture a historical baseline.

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
| Agent Profile, build, or installation contract | owning validator or safety negative-control | existing test module for the changed generator, builder, or installer |
| End-to-end routing manifest | agent-behavior sample | `evals/agent-behavior/samples/` |

## Failure Modes

- Claiming a routing, behavior, build, or installation effect without a failing
  case, relevant negative control, or existing evidence that catches regression.
- Adding a routing trigger with no over-routing guard, so the trigger silently
  widens routing.
- Writing a new rule that the agent can bypass with an unaddressed
  rationalization.
- Moving content to a reference without a loading policy, so it is never loaded.
- Letting the body grow instead of moving deep content to a reference.
