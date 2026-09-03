# Atomic Filesystem Commit And Containment

- Define exclusive temporary creation in the destination directory, a documented same-filesystem commit, atomic visibility, separate crash durability proof, legitimate concurrency, and bounded cleanup.

**Load when:** Local file creation, replacement, crash durability, path containment, link handling, protection, ownership, or cleanup can change the decision.

**Do not load when:** No local filesystem mutation or path-authority decision changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

Official sources were accessed on 2026-07-26.

## One Decision

Select one normal file-mutation contract whose target, commit point, concurrency, durability, and cleanup semantics hold across the supported target set. Split by platform or fail closed when one mechanism cannot satisfy that contract.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Destination and path grammar | Accept the consumer-owned relative forms and bind every operation to the intended destination | An absolute, parent, alternate-namespace, or link path reaches another object |
| Create or replace intent | Choose exclusive create, replace-if-present, or fail-if-present explicitly | A race changes which object is created or overwritten |
| Temporary identity and legitimate concurrency | Create a unique temporary object exclusively and retain its opened identity through the commit | Competing writers share a temporary name or commit an unowned object |
| Commit locality | Create the temporary object in the destination directory and verify the replacement stays on the required filesystem or volume | Cross-device failure or copy/delete fallback exposes partial state |
| Visibility and durability | Define atomic reader visibility separately from data and directory-metadata persistence after crash | Rename succeeds but acknowledged content or the final name is absent after recovery |
| Cleanup | Name temporary-object identity, cleanup authority, interruption behavior, and retained evidence | Cleanup removes another writer's object, hides the primary failure, or leaves an unowned artifact |

## Platform Constraints

- On POSIX targets, select directory-relative creation, replacement, synchronization, and cleanup operations from the supported runtime contract.
- POSIX `rename()` defines namespace replacement and reports cross-filesystem cases; it does not establish stable-storage durability by itself.
- On Windows, select create and replace APIs from the complete supported sharing, replacement, flush, and recovery contract.
- Use only documented guarantees of the supported storage target; an unsupported guarantee remains a Proof Limit rather than an invented hostile writer.

## Failure Rules

- Use exclusive creation to establish collision-free temporary intent.
- Preserve the original write, flush, close, or replace error while reporting cleanup failure separately.
- Reconcile the final name and bytes before retrying an interrupted or unknown commit result.
- Do not promise power-loss durability from a passing unit test or one successful flush call without recovery evidence.

## Primary Sources

- [POSIX `open()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html)
- [POSIX `rename()` and `renameat()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)
- [POSIX `fsync()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/fsync.html)
- [Microsoft moving and replacing files](https://learn.microsoft.com/en-us/windows/win32/fileio/moving-and-replacing-files)
- [Microsoft `FlushFileBuffers`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

## Proof Limits

These sources do not establish the repository's runtime wrapper, supported storage guarantees, or crash-recovery behavior. Exercise competing writers, interruption, cross-volume failure, cleanup ownership, and recovery for the changed path before closing those claims.
