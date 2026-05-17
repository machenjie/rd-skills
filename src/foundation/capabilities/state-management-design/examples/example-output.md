# Example Output

```markdown
## State Ownership Map

Server state:
- Project details come from GET /projects/:id.
- Freshness window is 60 seconds; save invalidates project detail and project list caches.

UI state:
- Active settings tab is route-derived.
- Expanded help panels are local to each section and reset on route change.

Form state:
- Settings draft is owned by SettingsForm.
- Draft resets after successful save or explicit cancel.
- If server data changes during editing, show conflict notice before overwrite.

Authentication state:
- Current identity and permissions come from the authenticated session endpoint.
- Expiry triggers reauthentication and clears privileged controls.

Global state decision:
- No global store; no state crosses unrelated routes.
```
