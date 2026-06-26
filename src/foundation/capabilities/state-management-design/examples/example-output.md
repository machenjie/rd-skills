# Example Output

```markdown
## State Ownership Map

mode_selected: server cache ownership + form draft lifecycle + auth and permission state

state_scope:
- Surface: project settings route.
- Owners: ProjectSettingsRoute owns query/cache decisions; SettingsForm owns editable draft; AuthProvider owns identity and permissions.
- Source evidence inspected: route loader, `useProjectQuery`, `useUpdateProjectMutation`, AuthProvider, existing settings form tests.
- graph_memory_trajectory_judgment: existing query client and auth provider accepted after source inspection; old localStorage permission helper rejected as stale pattern.

state_inventory:
- Project details: server state from `GET /projects/:id`; owned by query cache; read by settings panels; written by update mutation.
- Settings draft: form state owned by SettingsForm; created from project details only when edit starts; reset on save success, cancel, logout, or route leave confirmation.
- Active tab: UI state derived from route search param; reset by navigation.
- Current identity and permissions: auth/permission state from session endpoint; not read from localStorage.

server_state_config:
- `project.detail(projectId)`: staleTime 60 seconds, gcTime 10 minutes, stale-while-revalidate banner for risky edits.
- Save mutation invalidates project detail and project list caches.
- Logout, 401, and role-change events clear protected project caches.

auth_state_design:
- Session endpoint is the trusted source.
- 401 invalidates auth state, clears protected caches/storage, and redirects with returnTo.
- Cross-tab logout uses BroadcastChannel; if browser validation is not run, record that as residual risk.

form_state_design:
- Draft belongs to SettingsForm and is separate from server cache only during edit mode.
- If project data changes during editing, show conflict notice and require user choice before overwrite.
- Sensitive draft fields are not persisted; normal draft is discarded on cancel/logout.

optimistic_update_design:
- Name edit is not optimistic; save waits for server confirmation.
- Favorite toggle is optimistic: snapshot previous value, update immediately, rollback on failure, show error, invalidate detail cache on settle.

client_persistence_privacy_model:
- Theme preference persists in localStorage with versioned key and no logout clear requirement.
- Identity, permissions, tokens, project data, and sensitive drafts are not persisted in client-writable storage.

global_state_justifications:
- No new global store. State does not cross unrelated routes except AuthProvider and query cache.

derived_state_map:
- Display name and dirty-state indicator are computed from project details plus draft values; not stored separately.

race_conditions:
- Concurrent saves use server version conflict response; conflict state preserves draft and refetches canonical project data.
- Late query responses are scoped by projectId query key.

state_to_validation_map:
- Cache invalidation: mutation test.
- Logout clearing: auth provider test plus query cache assertion.
- Optimistic rollback: mutation failure test.
- Form conflict: component test.
- Cross-tab logout: manual browser check pending; residual risk recorded.

handoff_boundaries:
- `frontend-api-integration`: timeout, cancellation, response validation, and 401 request lifecycle.
- `form-validation-design`: field validation messages and submit authority.
- `security-privacy-gate`: token and sensitive draft persistence review.
- `frontend-testing`: executable cache/logout/rollback/race tests.

validation_evidence:
- Planned: component tests for save, conflict, logout clear, optimistic failure; query cache unit test for invalidation.

evidence_limits:
- No deployed browser cross-tab validation yet.
- Server-side permission enforcement is out of scope and must be proven by authentication/authorization review.
```
