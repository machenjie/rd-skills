# Browser Extension Lifecycle and Messaging

Load for browser extension manifests, execution contexts, background recovery, or messaging.
Skip ordinary websites, PWAs, and changes without a browser extension target.

## Decision Rules

- Bind manifest version, minimum browser version, APIs, and optional permissions to the supported target matrix.
- Distinguish page, content script, extension page, background worker, and native messaging contexts.
- Validate sender identity, origin or frame where relevant, message schema, and permitted operation.
- Keep privileged operations behind actual permission grants rather than trusting a message annotation.
- Persist only state that must survive worker termination; reconstruct transient state after activation.
- Make event handling safe when a worker stops between starting work and recording completion.
- Distinguish install, update, browser startup, and worker restart events.
- Migrate stored state across supported extension versions and preserve explicit recovery on partial upgrade.
- Release subscriptions, ports, and native-process resources according to their owners.
- Test permission revocation and late responses without reviving denied operations.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Page-derived message requests a privileged operation | Receiver checks sender, payload, and actual authority |
| Background worker is terminated between events | Required state recovers without relying on globals |
| Extension upgrades with old stored data | Migration preserves accepted state or reports recovery failure |
| Native messaging disconnects after a request | Outcome is reconciled before repeating an external effect |
| Permission is revoked before a late reply | Late completion cannot restore revoked capability |

## Proof Limits

- Chrome lifecycle and asynchronous message response behavior vary by version; verify the declared minimum target.
- Browser-extension evidence does not prove IDE-extension or mini-program behavior.

## Sources

- [Chrome service-worker lifecycle](https://developer.chrome.com/docs/extensions/develop/concepts/service-workers/lifecycle)
- [Chrome messaging contracts](https://developer.chrome.com/docs/extensions/develop/concepts/messaging)
