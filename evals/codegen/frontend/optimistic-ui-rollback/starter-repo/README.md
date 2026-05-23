# Starter Repo

## Stack

TypeScript React task list with local cache helper, API client, and Testing
Library style tests. The starter does not assume a specific remote cache
library, but the state boundary is isolated behind a task store module.

## Initial State

Archive click removes the task from the visible list and sends an API request.
On failure the UI only writes to the console. Pending state is global, rapid
clicks can send duplicate requests, and list selection can point to a removed
task.

## Files

- `src/tasks/TaskList.tsx` renders tasks and archive controls.
- `src/tasks/taskStore.ts` manages visible tasks and pending operations.
- `src/tasks/api.ts` calls the archive endpoint.
- `src/tasks/__tests__/TaskList.archive.test.tsx` covers the existing success path.
- `src/tasks/types.ts` defines task and archive response types.

## Constraints

Keep the visible workflow fast while treating the server response as the final
authority. Avoid adding a broad state management dependency unless the starter
already uses one.