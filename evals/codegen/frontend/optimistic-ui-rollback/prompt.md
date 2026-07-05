# Benchmark Prompt

## Task

Implement optimistic archive and rollback behavior for the project task list.
The starter UI removes a task immediately after archive click but never restores
it if the API fails or returns a conflict.

## Context

Tasks can be archived from a list view. The backend may reject the request when
the task has been completed by another user, moved to a locked project, or the
network request times out. Users need responsive UI without losing accurate
state.

## Requirements

- Optimistically remove or mark the task as archived after user action.
- Roll back the task to the correct position and state on failure.
- Show a recoverable error state with retry or undo behavior.
- Prevent duplicate archive requests for the same task while one is pending.
- Reconcile server returned task state when the archive succeeds with updated data.
- Add tests for success, failure rollback, conflict, timeout, and rapid repeated clicks.

## Constraints

- Do not mutate shared cached state in a way that other views cannot reconcile.
- Do not hide API failures in console logs only.
- Do not reload the whole page as the rollback mechanism.

## Deliverables

- Updated state management, task list component, API handling, and tests.
- State transition notes for optimistic, confirmed, failed, retried, and undone actions.
- Evidence that list ordering and selection state survive rollback.

## Completion Evidence

- Tests proving rollback restores item content, order, and action availability.
- Reliability note explaining timeout and retry behavior.
- Regression evidence for existing successful archive behavior.