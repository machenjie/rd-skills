# Test Suite

## Required Checks

- Successful archive optimistically updates and then confirms with server data.
- API failure restores the task at its original position with prior selection state.
- Conflict response restores task and displays a recoverable message.
- Timeout leaves retry or undo available and does not duplicate requests.
- Rapid repeated clicks for one task produce only one pending request.

## Fixtures

- Three task list with a selected middle item.
- Successful archive response with updated task version.
- Conflict response indicating locked project.
- Timeout or rejected promise from archive API.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Existing successful archive path remains visually responsive.
- Unrelated task actions remain available while one task is pending.
- Error message is dismissible and does not remove rollback state prematurely.