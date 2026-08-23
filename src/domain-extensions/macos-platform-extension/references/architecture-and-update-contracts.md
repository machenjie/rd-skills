# Architecture and Update Contracts

Load this Reference only when universal binaries, Apple Silicon/Intel support,
installation, updates, downgrade, or mixed app/API versions change.

Official Apple Developer pages below were accessed on 2026-07-24.

## Architecture Decision

- Read claimed architectures and deployment target from repository build and
  release configuration; inspect every app, framework, plug-in, XPC service,
  helper, and bundled executable in the final artifact.

## Update and Compatibility Decision

- Name the distribution channel and repository-declared updater or installer
  owner, feed/source, artifact identity, signature verification, install scope,
  atomicity, retry, rollback, downgrade, and recovery behavior.
- Require an official source for the selected updater or installer mechanism.
- Stop or mark independent self-update behavior unproven when the repository
  declares no mechanism or source.
- Define old-app/new-API and new-app/old-API combinations.
- Require client and API/provider evidence for each claimed combination.
- Reject backend-compatibility inference from packaging or notarization.

## Primary Sources

- [Building a universal macOS binary](https://developer.apple.com/documentation/apple-silicon/building-a-universal-macos-binary)
- [Distributing software on macOS](https://developer.apple.com/macos/distribution/)

## Source Limits

These rolling pages do not establish repository slices, Intel support,
deployment target, updater existence or correctness, feed authority, safe
rollback, installed-version population, server/API behavior, or release approval.
