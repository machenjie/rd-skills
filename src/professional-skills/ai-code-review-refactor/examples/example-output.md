# Example Output

Finding: High. Generated code calls `client.projects.archiveMany`, which does not exist in the SDK.

Impact: Runtime failure on archive action.

Fix: Use existing `client.projects.updateStatus` wrapper and preserve error mapping.

Test gap: Current test mocks the nonexistent method, so it cannot catch integration failure.

Refactor boundary: Do not introduce a new project client abstraction in this change.
