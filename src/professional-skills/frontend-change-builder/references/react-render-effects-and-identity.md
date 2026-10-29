# React Render, Effects, and Identity

**Reference type:** targeted
**Load when:** React rendering, component identity, dependency capture, or effect cleanup can change state or resource behavior.
**Do not load when:** The edit changes only CSS, copy, or established business logic without React lifecycle decisions.
**Required by:** task-agent
**Required output:** decision-record, validation-plan, proof-limit

## Decision Rules

- Keep rendering free of external subscriptions and mutations. An attempted render need not commit.
- Bind retained state to component type, tree position, and stable item keys when reordering requires state preservation.
- Treat a key change as a subtree reset, including form drafts, focus, and uncontrolled inputs.
- Treat an Effect as synchronization with an external system. Derive values during render when no external synchronization is needed.
- Include reactive values read by an Effect in its dependencies. Fix the capture or synchronization design before suppressing dependency diagnostics.
- Pair setup with cleanup for the same resource instance. Cleanup runs before replacement setup and when that Effect is removed.
- Distinguish passive Effects from layout Effects when measurement or pre-paint work matters. Effects do not run during server rendering.
- Exercise the configured development Strict Mode lifecycle for resource leaks across its extra setup/cleanup cycle.
- Abort or invalidate obsolete asynchronous work before a late result can overwrite the current selection.
- Keep business state authority explicit across props, local state, and external stores. Avoid effects that copy authoritative state into competing caches.

## Failure Scenarios

| Scenario | Observable check |
| --- | --- |
| Subscribe, cleanup, subscribe, then unmount | One live subscription while active; none after unmount |
| Reorder editable rows | Draft and focus stay with the intended item, not its old index |
| Change a dependency while its request is pending | A late result cannot replace the current result |
| Replace an entity using the same component position | The chosen key policy preserves or resets state deliberately |
| Abandon a render before commit | No external resource was acquired by render |

Return the identity policy, effect lifetime, stale-result handling, and exercised lifecycle boundaries.
Passing one development schedule does not prove all interleavings or production behavior.

## Version Sources

- Check the target React version against [Effect semantics](https://react.dev/reference/react/useEffect) and [state identity](https://react.dev/learn/preserving-and-resetting-state).
- Treat development Strict Mode behavior as a diagnostic configuration, not a universal production execution count.
