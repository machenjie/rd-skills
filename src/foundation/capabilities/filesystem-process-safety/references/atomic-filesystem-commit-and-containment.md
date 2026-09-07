# Atomic Filesystem Commit And Containment

- Identify the actual create, replace, attribute, or cleanup operation and its consumer guarantees.

**Load when:** Local file creation, replacement, crash durability, path containment, link handling, protection, ownership, or cleanup can change the decision.

**Do not load when:** No local filesystem mutation or path-authority decision changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

Official sources were accessed on 2026-07-26.

## One Decision

Choose a mutation contract covering target, commit, concurrency, durability, and cleanup across supported platforms. Split by platform or fail closed if one mechanism cannot satisfy it.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Destination and path grammar | Bind operations and accepted relative paths to the consumer-owned destination | An absolute, parent, alternate-namespace, or link path reaches another object |
| Operation intent | Choose create, replace, attribute-only mutation, or cleanup; temporary publication rules apply only to selected create/replace mechanisms | A race changes which object is created or overwritten |
| Temporary identity and legitimate concurrency | For temporary publication, create a unique object exclusively and retain its opened identity through commit | Competing writers share a temporary name or commit an unowned object |
| Commit locality | For temporary publication, create the object in the destination directory and verify replacement stays on the required filesystem or volume | Cross-device failure or copy/delete fallback exposes partial state |
| Required file attributes | Preserve or deliberately replace consumer-required mode/execute bits, owner, ACL, and other attributes using supported APIs and authority | Replacing an executable with a private temporary file drops execute permission, or replacement broadens access |
| Visibility and durability | Define atomic reader visibility separately from data and directory-metadata persistence after crash | Rename succeeds but acknowledged content or the final name is absent after recovery |
| Cleanup | Name the owned cleanup target and any temporary-object identity, authority, interruption behavior, and retained evidence | Cleanup removes another writer's object, hides the primary failure, or leaves an unowned artifact |

## Platform Constraints

- For POSIX, use supported directory-relative creation, replacement, synchronization, and cleanup.
- POSIX `rename()` defines namespace replacement and reports cross-filesystem cases; it does not establish stable-storage durability by itself.
- For Windows, choose create/replace APIs supporting the sharing, replacement, flush, and recovery contract.
- Use documented storage guarantees; unsupported guarantees remain Proof Limits, not evidence of a hostile writer.

## Failure Rules

Apply creation and commit checks to selected temporary publication. For attribute-only changes or cleanup, verify target identity, allowed mutation, concurrency, failure, and recovery without inventing a replacement.

- Create temporary objects exclusively.
- Establish required content and attributes on the owned temporary object before publication where supported.
- Order ownership and mode/ACL changes according to platform effects, then verify the required result; do not copy unrelated attributes blindly.
- If the platform requires an attribute change after replacement, define the visible intermediate state and recovery policy.
- Use another supported mechanism when that interval violates the consumer contract.
- Verify final object identity, bytes, and required attributes after commit.
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

These sources do not prove repository wrapper behavior, storage guarantees, or crash recovery. Test competing writers, interruption, cross-volume failure, cleanup ownership, and recovery before closing claims about the changed path.
