# Identity, Packaging, and Installation Contracts

Load this Reference only when packaged/unpackaged identity, MSIX, installation,
update, repair, or uninstall behavior changes the decision.

Official Microsoft Learn pages below were accessed on 2026-07-24.

## Identity Decision

- Record package identity, app identity, family/full names, executable identity,
  install scope, channel, dependencies, and upgrade lineage from final inputs.
- Separate packaged MSIX, packaged-with-external-location, and unpackaged
  deployment; identity-dependent APIs and registrations are not interchangeable.
- Name the repository-declared installer and updater owner for install, update,
  repair, uninstall, retry, rollback, data retention, and reboot behavior.
- Define identity and registration continuity plus downgrade, dependency,
  certificate, and repair responses across upgrades.

## Primary Sources

- [Package and deploy overview](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/)
- [Deployment overview](https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/deploy-overview)
- [Deploy unpackaged apps](https://learn.microsoft.com/en-us/windows/apps/windows-app-sdk/deploy-unpackaged-apps)
- [Managing MSIX deployment](https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-overview)
- [Differential MSIX updates](https://learn.microsoft.com/en-us/windows/msix/desktop/managing-your-msix-deployment-update)

## Source Limits

These rolling pages do not establish the repository manifest, identity,
installer technology, update feed, deployed population, rollback safety,
enterprise policy, or release approval.
