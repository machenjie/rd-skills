# Review Rubric

## Passing Standard

The solution must make switch fallthrough intentional or remove it, with branch
tests that prove suspended and active behavior independently.

## Scoring

- 35 percent fallthrough correctness.
- 25 percent branch regression tests.
- 20 percent C++ idiom quality.
- 10 percent API compatibility.
- 10 percent local scope restraint.

## Automatic Failure Conditions

- Silencing fallthrough warnings without clarifying behavior.
- Rewriting the status system for one switch statement.
- Reporting completion without suspended and active branch tests.
- Changing public enum names.

## Reviewer Notes

Strong answers keep the switch local and make the fallthrough decision visible.

