# Storage and Keystore Contracts

Load this Reference only when Android-local data, backup, account scope,
encryption, or key lifecycle changes.

Official Android Developers pages below were accessed on 2026-07-24.

## Data and Key Decision

- Classify data by sensitivity, durability, sharing, account, deletion, backup,
  migration, and offline requirements before choosing a storage location.
- Keep secrets and key material out of ordinary preferences, files, logs, and
  source; use Android Keystore only with a defined cryptographic purpose.
- Bind ciphertext to key alias, authentication policy, account identity, schema
  version, and recovery behavior.
- Decide whether backup includes, excludes, transforms, or invalidates each data
  class and its dependent key material.

## Failure Proof

- Exercise missing, invalidated, rotated, and authentication-gated keys.
- Exercise restore on another device, application upgrade/downgrade boundary,
  logout/account switch, partial migration, low storage, and corrupt records.
- Prove deletion removes all owned copies without deleting another account's data.

## Required Record

Return the data inventory, storage and key owner, backup rule, migration path,
identity binding, invalidation and recovery behavior, tested API/device scope,
proof limits, and residual risk.

## Primary Sources

- [Data and file storage](https://developer.android.com/training/data-storage)
- [Android Keystore system](https://developer.android.com/privacy-and-security/keystore)
- [Back up user data](https://developer.android.com/identity/data/autobackup)

## Source Limits

These rolling pages do not establish repository schemas, threat model, device
hardware security, backup transport, OEM behavior, or regulatory retention
requirements. Keystore use alone does not prove end-to-end data protection.
