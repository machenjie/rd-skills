# Desktop Entry, MIME, and Keyring Contracts

Load this Reference only when desktop entries, application IDs, MIME handlers,
activation, or desktop secret storage changes the decision.

Official freedesktop.org specifications below were accessed on 2026-07-24.

## Identity and Integration Decision

- Bind desktop-file ID, filename, application ID, executable, arguments,
  localized fields, icon, actions, D-Bus activation, package identity, and path.
- Bind MIME declarations and handler choice to installed metadata, user
  preference, activation payload validation, update, and uninstall cleanup.
- Do not overwrite user defaults merely because the application declares support.
- Record the actual keyring/Secret Service provider, collection, unlock policy,
  session, item attributes, account scope, migration, logout, and unavailable state.
- Never infer keyring availability, persistence, or unlock behavior across
  desktops, display managers, remote sessions, or headless execution.

## Primary Sources

- [Desktop Entry specification](https://xdg.pages.freedesktop.org/xdg-specs/desktop-entry/latest-single/)
- [MIME Applications specification](https://specifications.freedesktop.org/mime-apps/latest/)
- [Secret Service API](https://specifications.freedesktop.org/secret-service/latest/)

## Source Limits

These rolling specifications do not establish installed desktop databases,
package paths, user preferences, keyring provider/policy, sandbox access,
credential recovery, or observed desktop behavior.
