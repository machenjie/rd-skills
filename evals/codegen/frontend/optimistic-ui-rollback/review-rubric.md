# Review Rubric

## Passing Standard

The implementation must give a responsive archive interaction while preserving
server truth and user recovery on failure. Tests must prove rollback restores
the actual user visible list state, not just an internal flag.

## Scoring

- 30 percent behavior for optimistic success, rollback, conflict, timeout, and retry paths.
- 20 percent state design for snapshots, per task pending state, and cache reconciliation.
- 20 percent test quality for race prevention, order preservation, and user visible errors.
- 15 percent reliability for duplicate request prevention and observable failures.
- 15 percent maintainability for clear state transitions and limited dependencies.

## Automatic Failure Conditions

- Failed archive leaves the task missing or selected state corrupted.
- Duplicate requests can be sent for the same task action.
- API failures are hidden only in console output.
- Page reload is used as the recovery strategy.

## Reviewer Notes

The best solutions make optimistic state a reversible transition rather than a
special case scattered through the component. Favor small state machines and
user level tests over broad rewrites.