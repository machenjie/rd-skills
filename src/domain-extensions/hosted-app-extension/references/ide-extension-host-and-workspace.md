# IDE Extension Host and Workspace Boundaries

Load for IDE activation, workspace trust, remote execution, host processes, or extension upgrades.
Skip internal repository plugins without an IDE host lifecycle or capability contract.

## Decision Rules

- Bind contribution points, activation behavior, engine version, and extension placement to the actual host.
- Distinguish the UI extension host from a remote or workspace extension host.
- Resolve files and processes in the context that owns them rather than assuming the local machine.
- Gate workspace-driven execution on actual trust and capability requirements.
- Keep read-only inspection separate from executing workspace scripts or tools.
- Validate messages crossing webviews, host processes, or remote boundaries.
- Dispose registrations, subscriptions, timers, and processes when their owning activation or workspace ends.
- Restore necessary state after host restart without reusing stale workspace identity.
- Preserve supported configuration and stored-state migration across extension upgrades.
- Check that remote paths, credentials, and process results are not confused with local equivalents.

- Separate unload from uninstall using the target host contract; do not assume an uninstall callback exists.
- Define uninstall cleanup and retained durable state, external registrations, and grants according to their actual owners.
- Verify reinstall recovery against that retention policy, including externally retained registrations.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Extension opens in Restricted Mode | Features requiring trusted execution remain bounded |
| Workspace runs remotely while UI remains local | Paths and effects execute in their intended host |
| Host restarts with pending work | State and registrations recover without duplicate effects |
| Contribution activates on another supported version | Activation matches that version contribution contract |
| Webview sends a forged message | Receiver validates message identity and permitted operation |

| Uninstall then reinstall with retained external state | Cleanup and recovery follow the target host policy without duplicate registrations or revived grants |

## Proof Limits

- Some contributions activate implicitly on newer hosts; do not copy an older activationEvents rule to every version.

## Sources

- [VS Code activation events](https://code.visualstudio.com/api/references/activation-events)
- [VS Code remote extensions](https://code.visualstudio.com/api/advanced-topics/remote-extensions)
- [VS Code Workspace Trust source](https://raw.githubusercontent.com/microsoft/vscode-docs/main/api/extension-guides/workspace-trust.md)
