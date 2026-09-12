# Tauri Framework Contracts

Load when Tauri commands, capabilities, links, or bundles affect the change;
skip when those boundaries and platform behavior remain unchanged.

## Decision Rules

- When a privileged webview call changes, inspect the effective permission union at the existing native capability/permission owner: overlapping capabilities merge.
- Application commands registered with `invoke_handler` are available to all windows/webviews by default; when caller isolation is required, use the app-command permission mechanism (`AppManifest::commands` and app permissions). A restrictive plugin capability alone does not restrict custom application commands.
- Let the existing lifecycle/link owner handle startup links with `getCurrent` and running-app links with `onOpenUrl`. Route both through the existing handler, validating URL shape and preserving its duplicate-delivery semantics. Later events update `getCurrent`, so it is not immutable evidence of a cold start.
- For Windows/Linux delivery to an existing instance, the native bootstrap owner configures the single-instance plugin with its deep-link feature and registers it first; `onOpenUrl` is unsupported there without that setup. Retain the returned unlisten function when registration resolves and call it at owner cleanup, including when disposal precedes registration completion. Do not trust CLI arguments as proof of an authentic OS link.
- Before adapting mismatched APIs, the dependency/bootstrap owner checks Cargo and JavaScript lockfiles, plugin initialization and capability identifiers.
- Tauri requires matching minor versions of `@tauri-apps/api` and the `tauri` crate. Check each plugin's own compatibility contract instead of extending that rule to every plugin pair.
- Validate native registration and the affected packaged target; a development webview cannot establish installer behavior.

## Sources And Version Limit

Sources checked 2026-09-12: [capabilities](https://v2.tauri.app/security/capabilities/), [deep linking](https://v2.tauri.app/plugin/deep-linking/), [onOpenUrl](https://v2.tauri.app/reference/javascript/deep-link/#onopenurl), [dependency versions](https://v2.tauri.app/develop/updating-dependencies/#sync-npm-packages-and-cargo-crates-versions), and [distribution](https://v2.tauri.app/distribute/).
Version limit: these are Tauri 2 contracts. Check repository pins and supported targets; they do not establish Tauri 1 behavior, every plugin's mobile support, target triples, signing, or installer behavior.
