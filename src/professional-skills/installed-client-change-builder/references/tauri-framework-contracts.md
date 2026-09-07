# Tauri Framework Contracts

Use this Reference only for the named tauri-framework-contracts decision.

## Decision Rules

- Keep commands, plugins, capabilities, and webview callers inside their declared authority.
- Validate deep-link registration and the platform-specific bundle output.

## Sources And Version Limit

Sources: [capabilities](https://v2.tauri.app/security/capabilities/), [deep linking](https://v2.tauri.app/plugin/deep-linking/), and [distribution](https://v2.tauri.app/distribute/).
Version limit: these are Tauri 2 pages. They do not establish plugin versions, mobile support, target triples, signing, or installer behavior.
