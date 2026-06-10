# Review Rubric

## Passing Standard

The solution passes when lock scope protects only the named invariant and does
not include network or storage IO.

## Scoring

- 30 percent invariant and lock-scope design.
- 25 percent removal of IO from the critical section.
- 20 percent deadlock, timeout, and conflict behavior.
- 15 percent stress, race, or lock-contention evidence.
- 10 percent structure placement and side-effect visibility.

## Automatic Failure Conditions

- Lock held across network or storage IO remains.
- No timeout behavior is declared.
- No deadlock analysis.
- No stress or race evidence.
- Side effects are emitted before invariant commit safety is addressed.

## Reviewer Notes

Reward small critical sections and explicit side-effect boundaries. Penalize
locks that serialize IO-bound work.
