# Review Rubric

## Passing Standard

The solution passes when it produces a tagged complexity delete list that safely
removes or shrinks unnecessary structure while preserving behavior and safety
gates.

## Scoring

- 35 percent tagged delete/shrink/reuse/YAGNI finding quality.
- 25 percent behavior-preservation and caller-search evidence.
- 20 percent rejection of wrapper-only and one-implementation abstractions.
- 15 percent regression evidence.
- 5 percent residual risk and next gate clarity.

## Automatic Failure Conditions

- Wrapper-only delegation is approved without a real boundary.
- One-implementation interface, factory, or strategy is kept for future proofing.
- Delete recommendation lacks caller search and regression evidence.
- Fewer lines is treated as approval while boundaries, side effects, or public behavior are lost.

## Reviewer Notes

This benchmark evaluates review judgment. A passing answer may retain some
complexity, but only with current force, validation evidence, and residual risk.
