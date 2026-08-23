# Atomic Filesystem Commit And Containment

- Define exclusive temporary creation in the destination directory, restrictive protection, documented same-filesystem commit, atomic visibility, and separate crash-durability proof.

**Load when:** Local file creation, replacement, crash durability, path containment, link handling, protection, ownership, or cleanup can change the decision.

**Do not load when:** No local filesystem mutation or path-authority decision changes.

**Required by:** `analysis-agent`, `task-agent`, `review-agent`

**Required output:** `boundary-decision`, `proof-limit`, `residual-risk`

Official sources were accessed on 2026-07-26.

## One Decision

Select one file-mutation contract whose authority, commit point, protection, durability, and cleanup semantics hold across the supported target set. Split by platform or fail closed when one mechanism cannot satisfy the shared contract.

| Fact to establish | Required decision | Failure signal |
|---|---|---|
| Trusted base and path grammar | Accept the consumer-owned relative forms and reject the rest; bind traversal to an already-open trusted directory or an equivalent platform capability | Absolute, parent, alternate namespace, link, reparse, or mount traversal reaches another object |
| Create or replace intent | Choose exclusive create, replace-if-present, or fail-if-present explicitly | A race changes which object is created or overwritten |
| Commit locality | Create the temporary object in the destination directory and verify the replacement stays on the required filesystem or volume | Cross-device failure or copy/delete fallback exposes partial state |
| Visibility and durability | Define atomic reader visibility separately from data and directory-metadata persistence after crash | Rename succeeds but acknowledged content or the final name is absent after recovery |
| Protection and identity | Apply creation-time mode or security descriptor, ownership, inheritance, and replacement-metadata policy | Bytes are briefly overexposed or the final object receives the wrong ACL, owner, or mode |
| Cleanup | Name temporary-object identity, cleanup authority, interruption behavior, and retained evidence | Cleanup removes an unrelated path, hides the primary failure, or leaves an unowned artifact |

## Platform Constraints

- On POSIX targets, use directory-relative operations and component link controls where available. `O_NOFOLLOW` on one open does not by itself prove that every earlier path component stayed under the trusted base.
- POSIX `rename()` gives specified namespace replacement behavior and reports cross-filesystem cases; it does not by itself establish stable-storage durability. Derive file and containing-directory synchronization from the target filesystem and runtime, and record unsupported guarantees.
- On Windows, resolve executable filesystem behavior through handle-based APIs and an explicit reparse-point policy. A path string that was normalized or inspected earlier can be redirected before a later open.
- Select the Windows mutation API from its complete target-platform contract.
- Verify the final security descriptor when the selected API can preserve or substitute protection.
- Treat network, overlay, removable, encrypted, virtual, and memory filesystems as distinct targets when their documented guarantees can change commit, flush, sharing, link, or recovery behavior.

## Failure Rules

- Reject predictable temporary names.
- Use exclusive creation instead of create-then-check for the collision and authorization decision.
- Reject canonicalize/check/reopen sequences for attacker-writable ancestors. Keep validation and mutation bound to the same trusted directory and opened object.
- Preserve the original write, flush, close, or replace error while reporting cleanup failure separately.
- Do not promise power-loss durability from a passing unit test or successful flush call without target-filesystem and recovery evidence.

## Primary Sources

- [POSIX `open()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/open.html)
- [POSIX `rename()` and `renameat()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/rename.html)
- [POSIX `fsync()`](https://pubs.opengroup.org/onlinepubs/9799919799/functions/fsync.html)
- [Microsoft moving and replacing files](https://learn.microsoft.com/en-us/windows/win32/fileio/moving-and-replacing-files)
- [Microsoft `CreateFileW`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew)
- [Microsoft reparse points and file operations](https://learn.microsoft.com/en-us/windows/win32/fileio/reparse-points-and-file-operations)
- [Microsoft file security and access rights](https://learn.microsoft.com/en-us/windows/win32/fileio/file-security-and-access-rights)
- [Microsoft `FlushFileBuffers`](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-flushfilebuffers)

## Proof Limits

These specifications and rolling vendor pages do not establish the repository's supported runtime versions, wrapper behavior, effective filesystem, mount options, storage hardware, ACL inheritance, antivirus/filter drivers, crash recovery, or attacker-writable ancestors. Record those facts and run representative race, interruption, permission, cross-volume, and recovery checks before closing the corresponding claim.
