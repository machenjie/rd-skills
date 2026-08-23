# Packaging, Installation, and Update Contracts

Load this Reference only when Flatpak, Snap, AppImage, deb, rpm, sandbox,
installation, update, rollback, or distribution behavior changes the decision.

Official maintainer and distribution pages below were accessed on 2026-07-24.

## Package Decision

- Read the final package format, manifest/spec, runtime/base, architecture,
  dependencies, permissions/confinement, application ID, channel, and signatures.
- Keep Flatpak, Snap, AppImage, deb, and rpm identities, dependency resolution,
  confinement, integration, install scope, update, rollback, and removal separate.
- Name the repository-declared installer/update owner, source, atomicity, retry,
  data migration, downgrade, rollback, and recovery for the selected format.
- Inspect installed desktop/MIME/D-Bus/portal integration and executable/library
  resolution; a built artifact proves no installed behavior.
- Route distribution/update approval and rollout to `delivery-release-gate`.

## Primary Sources

- [Flatpak basic concepts](https://docs.flatpak.org/en/latest/basic-concepts.html)
- [Snap confinement](https://snapcraft.io/docs/explanation/security/snap-confinement/)
- [AppImage packaging guide](https://docs.appimage.org/packaging-guide/index.html)
- [Debian Policy](https://www.debian.org/doc/debian-policy/index.html)
- [RPM documentation](https://rpm.org/docs/)

## Source Limits

These rolling/versioned pages do not establish repository package definitions,
distribution policy, enabled repositories, dependency availability, signing
authority, update population, rollback safety, or rollout approval.
