# Example Output

Entity: Project.

Rule change: Archived projects cannot accept new tasks.

Invariant: A task may not be created when `project.status = archived`.

Authority: Backend domain service and database constraint where feasible.

Event: `ProjectArchived` is emitted after state transition.

Tests: state transition, forbidden task creation, event payload, audit record.
