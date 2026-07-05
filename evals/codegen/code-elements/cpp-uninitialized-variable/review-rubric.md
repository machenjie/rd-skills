# Review Rubric

## Passing Standard

The fix must prove the variable is initialized before every read and preserve the
public status contract without suppressing diagnostics.

## Scoring

- 35 percent initialization correctness.
- 25 percent branch regression evidence.
- 20 percent C++ idiom and diagnostic handling.
- 10 percent API compatibility.
- 10 percent handoff clarity.

## Automatic Failure Conditions

- Suppressing uninitialized-variable warnings.
- Adding global state or a new helper file for a local branch bug.
- Reporting completion without branch regression evidence.
- Changing enum/API values without compatibility rationale.

## Reviewer Notes

Strong answers prefer simple local initialization or explicit return branches.

