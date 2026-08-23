# Navigation and Restoration Contracts

Use this Reference only for the named navigation-and-restoration-contracts decision.

## Decision Rules

- Model initial load, same-document history, reload, back and forward, cancellation, and scroll or focus restoration as distinct entries.
- Bind page hide and show, persisted BFCache return, visibility changes, stale resources, paused work, and discarded-document recovery.
- When restoration can bypass a new load, model the restored entry independently from component mount.
- Return stale session or connection handling, current HTML navigation evidence, and browser-specific limits.

Reject a navigation model that ignores history traversal, BFCache, restored storage, or an active service worker.
