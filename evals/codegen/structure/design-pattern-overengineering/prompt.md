# Benchmark Prompt

## Task

Implement one simple discount eligibility rule while deciding whether a design
pattern is justified.

## Context

The starter repository has a straightforward order discount module. An
AI-generated patch proposes `DiscountStrategy`, `DiscountStrategyFactory`,
`BaseDiscountRule`, and a public `DiscountRuleProvider` interface even though
there is one current rule and no committed provider variation.

## Requirements

- Produce a Design Pattern Decision Record before accepting any pattern.
- Prefer direct code or a module-local helper when the single rule is clearer.
- Reject strategy, factory, public interface, and abstract base class unless a
  current variation force exists.
- Keep related private helpers in the existing owner file unless a real object
  or module boundary is proven.
- Add public behavior tests for eligible and ineligible discounts.

## Constraints

- Do not create a strategy with one implementation.
- Do not create a factory that only hides a simple constructor or function call.
- Do not use an abstract base class only for code reuse.
- Do not export an interface with no current consumer.

## Deliverables

- Updated discount rule implementation.
- Public behavior tests for the rule.
- Design Pattern Decision Record with rejected candidates, simpler alternative,
  object relationship, method placement, file impact, and tests.

## Completion Evidence

- Tests fail if the rule behavior is removed.
- Review evidence rejects pattern overengineering and public API expansion.
- The final structure has no speculative strategy, factory, registry, provider,
  or abstract base class.
