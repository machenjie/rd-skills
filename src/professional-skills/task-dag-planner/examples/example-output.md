# Example Output

Task A: Add compatible API field behind server default. Dependencies: none. Evidence: contract test.

Task B: Update frontend display using optional field. Dependencies: A. Evidence: component and E2E tests.

Task C: Add migration for derived index. Dependencies: A. Evidence: migration dry-run and rollback note.

Task D: Release with flag enabled for internal users. Dependencies: A, B, C. Evidence: dashboard and smoke test.
