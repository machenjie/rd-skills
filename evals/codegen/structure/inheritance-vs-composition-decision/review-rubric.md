# Review Rubric

## Passing Standard

The solution passes when it rejects inheritance for code sharing alone or proves
a real substitutable taxonomy with contract tests, and it preserves payment
behavior through public tests.

## Scoring

- 30 percent inheritance vs composition decision quality.
- 25 percent substitutability, base contract, and initialization safety evidence.
- 20 percent composition/delegation/helper placement for shared technical code.
- 15 percent contract and public behavior tests.
- 10 percent clarity and local naming convention.

## Automatic Failure Conditions

- Abstract base class exists only for code reuse.
- Subtype forces caller branching.
- No base contract tests or subtype contract tests.
- Initialization safety is not addressed.
- Strategy is introduced with one implementation and no current variants.

## Reviewer Notes

Reward boring composition when taxonomy is weak. Inheritance must pay its public
contract cost with actual substitutability evidence.
