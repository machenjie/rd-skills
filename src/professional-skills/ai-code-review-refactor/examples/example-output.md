# Example Output

## Review Scope

### Reviewed files

- `src/projects/archive-projects.ts`
- `tests/projects/archive-projects.test.ts`

### Unreviewed files

None.

## Finding

- Severity: High
- Evidence: Generated code calls `client.projects.archiveMany`, which does not exist in the SDK.
- Impact: Runtime failure on archive action.
- Fix: Use the existing `client.projects.updateStatus` wrapper and preserve error mapping.
- Test gap: The current test mocks the nonexistent method, so it cannot catch integration failure.
- Refactor boundary: Do not introduce a new project client abstraction in this change.
