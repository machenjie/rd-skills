# Electron Framework Contracts

Use this Reference only for the named electron-framework-contracts decision.

## Decision Rules

- Keep lifecycle and privileged operating-system work in the main-process owner.
- Validate renderer-to-main boundaries, deep-link entry, and the packaged artifact.

## Sources And Version Limit

Sources: [process model](https://www.electronjs.org/docs/latest/tutorial/process-model), [deep links](https://www.electronjs.org/docs/latest/tutorial/launch-app-from-url-in-another-app), [security](https://www.electronjs.org/docs/latest/tutorial/security), and [distribution](https://www.electronjs.org/docs/latest/tutorial/distribution-overview).
Version limit: `latest` can describe a development branch. Match the repository's Electron major and bundled Chromium and Node versions.
