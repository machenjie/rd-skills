# Review Rubric

## Passing Standard

The solution passes when it merges only the boundary-free private helper,
preserves the small files that own real boundaries, and proves behavior,
public contracts, import/export surfaces, and dependency direction before and
after the merge.

## Scoring

- 30 percent merge restraint: adapter/client, value object, and policy files
  remain separate with boundary rationale.
- 25 percent small-file merge: the tiny private helper is merged into the
  owning service only when behavior and readability stay stable.
- 20 percent refactoring evidence: import/export before/after, public contract
  preserved, dependency direction preserved, and behavior test before/after are
  documented.
- 15 percent clarity: navigation cost improves or stays no worse, and the
  next-change location is clearer after the helper merge.
- 10 percent tests: public behavior tests cover service orchestration, policy
  behavior, value object invariants, and adapter boundary behavior.

## Automatic Failure Conditions

- Merges adapter into service and hides side effects.
- Merges value object invariant into procedural owner.
- Merges independent policy with tests into orchestration.
- Reduces file count but increases mixed responsibility.
- Breaks dependency direction or public contract clarity.
- Hides side-effect boundary or removes a public behavior test boundary.
- Omits rejected-merge rationale for any small file with a real boundary.

## Reviewer Notes

Reward consolidation only when the file has no independent owner or boundary.
Penalize solutions that treat file count as the goal. A small file is valid
when it protects an adapter, value object invariant, policy contract, generated
surface, side effect, or dependency-direction boundary.
